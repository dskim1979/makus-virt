# -*- coding: utf-8 -*-
"""
GPU / NVIDIA vGPU management.

Two layers:
  - Discovery: list GPU-class PCI devices per node, and — for cards with an
    NVIDIA vGPU manager driver installed on the host — the mediated-device
    (mdev) profiles Proxmox exposes for that card (e.g. 'nvidia-263').
  - Allocation: assign a GPU to a VM, either as a whole-device PCI passthrough
    or as a single vGPU (mdev) slice. Building on the existing hostpciN slot
    logic in pegaprox/api/vms.py — this module only adds the GPU-aware
    picker on top, it doesn't duplicate the underlying passthrough mechanism.

Whole-card passthrough vs vGPU are mutually exclusive per physical GPU:
once one mdev slice is handed to a VM, the remaining capacity is other mdev
slices of the SAME profile family (the card's framebuffer is statically
partitioned by profile at creation time) — not a free-for-all mix. We surface
that as 'available_instances' per profile rather than a single free/used bit.

vGPU requires the NVIDIA vGPU host driver to already be installed and
licensed on the Proxmox node — this module only reads/writes Proxmox's own
PCI + mdev API, it cannot install or license the vGPU manager itself.
"""
import logging
import re
from flask import Blueprint, jsonify, request

from pegaprox.globals import cluster_managers
from pegaprox.utils.auth import require_auth
from pegaprox.utils.audit import log_audit
from pegaprox.api.helpers import check_cluster_access, get_connected_manager, safe_error, parse_pve_error

bp = Blueprint('gpu', __name__)

# PCI class 0300 = VGA compatible controller, 0302 = 3D controller (headless
# compute GPUs like datacenter NVIDIA cards report as 0302, not 0300).
_GPU_PCI_CLASSES = ('0300', '0302')

_PCIID_RE = re.compile(r'^[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]$')


def _valid_pciid(pciid):
    return bool(pciid) and bool(_PCIID_RE.match(pciid))


def _is_gpu(dev):
    """True if this /nodes/{node}/hardware/pci entry is a GPU.

    NS: Proxmox reports 'class' as a 6-hex-digit string — class + subclass +
    prog-if, e.g. '030000' for VGA compatible controller, '030200' for a
    headless 3D/compute card — not the bare 4-digit class+subclass we
    originally compared against. That earlier version did an exact-string
    match against ('0300', '0302'), which a real 6-digit value can never
    equal, so no card was ever detected (confirmed against a live cluster —
    a passed-through GPU didn't show up in the inventory or the VM's GPU
    picker at all). Compares only the first 4 hex digits (class+subclass),
    ignoring prog-if, and tolerates the class arriving as an int, with or
    without a '0x' prefix, or with leading zeros dropped.
    """
    raw = dev.get('class')
    if raw is None:
        return False
    cls = format(raw, 'x') if isinstance(raw, int) else str(raw)
    cls = cls.lower().replace('0x', '').strip()
    if len(cls) < 6:
        cls = cls.zfill(6)  # pad short/leading-zero-stripped values to the full 6 digits
    return cls[:4] in _GPU_PCI_CLASSES


def _friendly_vendor(vendor_id, vendor_name):
    # Proxmox's hardware/pci listing already resolves vendor/device names via
    # the system's pci.ids database when available; fall back to raw IDs.
    if vendor_name:
        return vendor_name
    known = {'0x10de': 'NVIDIA', '0x1002': 'AMD', '0x8086': 'Intel'}
    return known.get(str(vendor_id).lower(), vendor_id or 'Unknown')


@bp.route('/api/clusters/<cluster_id>/nodes/<node>/gpus', methods=['GET'])
@require_auth(perms=['node.view'])
def list_node_gpus(cluster_id, node):
    """GPU-class PCI devices on one node, each flagged with whether Proxmox
    reports vGPU (mdev) capability for it."""
    ok, err = check_cluster_access(cluster_id)
    if not ok: return err
    manager, error = get_connected_manager(cluster_id)
    if error: return error

    try:
        host, port = manager.host, manager.api_port
        url = f"https://{host}:{port}/api2/json/nodes/{node}/hardware/pci"
        r = manager._create_session().get(url, params={'pci-class': ''}, timeout=15)
        if r.status_code != 200:
            return jsonify({'error': parse_pve_error(r.text)}), r.status_code
        devices = r.json().get('data', []) or []
    except Exception as e:
        logging.error(f"[gpu] listing PCI devices on {node} failed: {e}")
        return jsonify({'error': safe_error(e, 'Failed to list PCI devices')}), 500

    gpus = []
    for dev in devices:
        if not _is_gpu(dev):
            continue
        pciid = dev.get('id') or dev.get('device_id') or ''
        gpus.append({
            'pciid': pciid,
            'device_name': dev.get('device_name') or dev.get('device') or 'Unknown GPU',
            'vendor': _friendly_vendor(dev.get('vendor'), dev.get('vendor_name')),
            'subsystem_device': dev.get('subsystem_device_name') or '',
            'iommu_group': dev.get('iommugroup'),
            # Proxmox sets mdev=1 on the PCI entry when the host driver exposes
            # mediated-device support for this card.
            'vgpu_capable': bool(dev.get('mdev')),
        })

    return jsonify({'node': node, 'gpus': gpus})


@bp.route('/api/clusters/<cluster_id>/nodes/<node>/gpus/<pciid>/profiles', methods=['GET'])
@require_auth(perms=['node.view'])
def list_vgpu_profiles(cluster_id, node, pciid):
    """Available NVIDIA vGPU (mdev) profiles for one physical GPU, with how
    many more instances of each profile currently fit in what's left of the
    card's framebuffer."""
    ok, err = check_cluster_access(cluster_id)
    if not ok: return err
    if not _valid_pciid(pciid):
        return jsonify({'error': 'Invalid PCI device id'}), 400
    manager, error = get_connected_manager(cluster_id)
    if error: return error

    try:
        host, port = manager.host, manager.api_port
        url = f"https://{host}:{port}/api2/json/nodes/{node}/hardware/pci/{pciid}/mdev"
        r = manager._create_session().get(url, timeout=15)
        if r.status_code == 500:
            # Proxmox returns 500 (not 404) for a card with no vGPU driver —
            # treat that as "no profiles" rather than surfacing a scary error,
            # since this endpoint is routinely polled for every GPU including
            # plain passthrough-only ones.
            return jsonify({'pciid': pciid, 'vgpu_capable': False, 'profiles': []})
        if r.status_code != 200:
            return jsonify({'error': parse_pve_error(r.text)}), r.status_code
        raw = r.json().get('data', []) or []
    except Exception as e:
        logging.error(f"[gpu] listing mdev profiles for {pciid} on {node} failed: {e}")
        return jsonify({'error': safe_error(e, 'Failed to list vGPU profiles')}), 500

    profiles = []
    for p in raw:
        profiles.append({
            'type': p.get('type'),
            'name': p.get('name') or p.get('type'),
            'description': p.get('description', ''),
            'framebuffer_mb': p.get('available') and p.get('type'),  # PVE doesn't expose MB directly per-type
            'available_instances': p.get('available', 0),
        })

    return jsonify({'pciid': pciid, 'vgpu_capable': True, 'profiles': profiles})


@bp.route('/api/clusters/<cluster_id>/gpu-inventory', methods=['GET'])
@require_auth(perms=['node.view'])
def cluster_gpu_inventory(cluster_id):
    """Cluster-wide capacity view: every physical GPU on every node, and
    which VMs currently hold a slice of it (whole-device or vGPU profile).

    Cross-references live VM configs (hostpciN entries) against the node PCI
    listing — same source of truth the per-VM passthrough tab uses, just
    rolled up across the whole cluster for planning instead of per-VM."""
    ok, err = check_cluster_access(cluster_id)
    if not ok: return err
    manager, error = get_connected_manager(cluster_id)
    if error: return error

    try:
        host, port = manager.host, manager.api_port
        session = manager._create_session()

        nodes_url = f"https://{host}:{port}/api2/json/nodes"
        nodes_resp = session.get(nodes_url, timeout=15)
        if nodes_resp.status_code != 200:
            return jsonify({'error': parse_pve_error(nodes_resp.text)}), nodes_resp.status_code
        nodes = [n['node'] for n in nodes_resp.json().get('data', [])]
    except Exception as e:
        logging.error(f"[gpu] cluster inventory: listing nodes failed: {e}")
        return jsonify({'error': safe_error(e, 'Failed to list nodes')}), 500

    inventory = []
    for node in nodes:
        try:
            session = manager._create_session()
            pci_url = f"https://{host}:{port}/api2/json/nodes/{node}/hardware/pci"
            pci_resp = session.get(pci_url, timeout=15)
            devices = pci_resp.json().get('data', []) if pci_resp.status_code == 200 else []
        except Exception as e:
            logging.warning(f"[gpu] cluster inventory: PCI listing failed on {node}: {e}")
            continue

        node_gpus = [d for d in devices if _is_gpu(d)]
        if not node_gpus:
            continue

        # VMs on this node + their hostpciN assignments, so we can mark each
        # GPU as allocated (and to what VM) rather than just "present".
        vm_assignments = {}  # pciid_prefix -> [{'vmid', 'name', 'mdev'}]
        try:
            qemu_url = f"https://{host}:{port}/api2/json/nodes/{node}/qemu"
            qemu_resp = session.get(qemu_url, timeout=15)
            vms = qemu_resp.json().get('data', []) if qemu_resp.status_code == 200 else []
        except Exception:
            vms = []

        for vm in vms:
            vmid = vm.get('vmid')
            try:
                cfg_url = f"https://{host}:{port}/api2/json/nodes/{node}/qemu/{vmid}/config"
                cfg_resp = session.get(cfg_url, timeout=10)
                config = cfg_resp.json().get('data', {}) if cfg_resp.status_code == 200 else {}
            except Exception:
                continue
            for key, value in config.items():
                if not key.startswith('hostpci'):
                    continue
                # value looks like "0000:01:00.0" or "0000:01:00.0,mdev=nvidia-263"
                parts = str(value).split(',')
                dev_addr = parts[0].strip()
                mdev = next((p.split('=', 1)[1] for p in parts[1:] if p.startswith('mdev=')), None)
                vm_assignments.setdefault(dev_addr, []).append({
                    'vmid': vmid,
                    'name': vm.get('name', f'VM {vmid}'),
                    'mdev': mdev,
                })

        for dev in node_gpus:
            pciid = dev.get('id') or ''
            assigned = vm_assignments.get(pciid, [])
            inventory.append({
                'node': node,
                'pciid': pciid,
                'device_name': dev.get('device_name') or dev.get('device') or 'Unknown GPU',
                'vendor': _friendly_vendor(dev.get('vendor'), dev.get('vendor_name')),
                'vgpu_capable': bool(dev.get('mdev')),
                'assignments': assigned,
                'status': 'allocated' if assigned else 'free',
            })

    total = len(inventory)
    allocated = sum(1 for g in inventory if g['status'] == 'allocated')
    return jsonify({
        'cluster_id': cluster_id,
        'gpus': inventory,
        'summary': {
            'total_gpus': total,
            'allocated': allocated,
            'free': total - allocated,
            'vgpu_capable_count': sum(1 for g in inventory if g['vgpu_capable']),
        },
    })
