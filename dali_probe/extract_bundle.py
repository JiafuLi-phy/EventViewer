#!/usr/bin/env python3
"""
Unified NPZ extraction script.
Auto-detects data source (DALI/Midway3) and available data types.

Usage:
    python extract_bundle.py --run 023756 --n 50        # Midway3: peak_basics + positions
    python extract_bundle.py --run 043864 --n 200       # DALI: real peaks
    python extract_bundle.py --run 044116 --n 100       # DALI: real peaks
    python extract_bundle.py --batch 023756,043864,044116 --n 50  # batch mode

Output: events_{run}_bundle.npz
"""
import argparse, os, sys, json, warnings, numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from event_plotter import io


def extract_run(run_id, n_events=50, s1_min=500, s2_min=50000, output_dir='.'):
    print(f'\n{"="*50}')
    print(f'Extracting run {run_id} ({n_events} events)')
    print(f'{"="*50}')

    # Find data directories
    storage_dirs = [
        '/project/lgrandi/xenonnt/processed/',
        '/project2/lgrandi/xenonnt/processed/',
        '/dali/lgrandi/xenonnt/processed/',
    ]
    existing = [d for d in storage_dirs if os.path.isdir(d)]

    # Load events
    events = None
    for sd in existing:
        evt_dir = io.find_data_dir(run_id, 'event_info', [sd])
        if evt_dir and 'event_info' in evt_dir:
            events = io.load_strax_chunks(run_id, 'event_info', [sd])
            break
    if events is None:
        for sd in existing:
            evt_dir = io.find_data_dir(run_id, 'event_basics', [sd])
            if evt_dir and 'event_basics' in evt_dir:
                events = io.load_strax_chunks(run_id, 'event_basics', [sd])
                break
    if events is None:
        print(f'ERROR: No event data found for run {run_id}')
        return None
    print(f'Events: {len(events)}')

    # Select events
    mask = np.ones(len(events), dtype=bool)
    if 's1_area' in events.dtype.names:
        mask &= events['s1_area'] > s1_min
    if 's2_area' in events.dtype.names:
        mask &= events['s2_area'] > s2_min
    sel = events[mask]
    sel = sel[np.argsort(sel['s2_area'])[::-1][:n_events]]
    sel = sel[np.argsort(sel['time'])]
    print(f'Selected: {len(sel)} events')

    # Load PMT data
    pmt_pos = io.load_pmt_geometry()
    to_pe = io.load_to_pe(n_channels=len(pmt_pos))

    # Try to load peaks (prefer real data)
    peaks = None
    is_real_data = False
    for dtype in ['peaks', 'peaklets', 'peak_basics']:
        for sd in existing:
            d = io.find_data_dir(run_id, dtype, [sd])
            if d and dtype in d:
                peaks = io.load_strax_chunks(run_id, dtype, [sd])
                is_real_data = dtype in ('peaks', 'peaklets')
                print(f'Loaded {len(peaks)} from {dtype} (real={is_real_data})')
                break
        if peaks is not None:
            break
    if peaks is None:
        print(f'ERROR: No peak data found')
        return None

    # Load CNN positions
    positions = None
    for sd in existing:
        d = io.find_data_dir(run_id, 'peak_positions_cnn', [sd])
        if d:
            positions = io.load_strax_chunks(run_id, 'peak_positions_cnn', [sd])
            print(f'Loaded {len(positions)} CNN positions')
            break

    # Load EAC
    eac = None
    for sd in existing:
        d = io.find_data_dir(run_id, 'event_area_per_channel', [sd])
        if d:
            eac = io.load_strax_chunks(run_id, 'event_area_per_channel', [sd])
            print(f'Loaded EAC data')
            break

    # Match peaks to events
    import strax
    fci_pk = strax.fully_contained_in(peaks, sel)
    fci_ps = strax.fully_contained_in(positions, sel) if positions is not None else None
    fci_ec = strax.fully_contained_in(eac, sel) if eac is not None else None

    peaks_list, pos_list, eac_list = [], [], []
    for i in range(len(sel)):
        ev_pk = peaks[fci_pk == i]
        peaks_list.append(ev_pk)

        # Match positions to peaks
        pk_x = np.full(len(ev_pk), np.nan)
        pk_y = np.full(len(ev_pk), np.nan)
        if positions is not None and fci_ps is not None:
            ev_ps = positions[fci_ps == i]
            for j, pk in enumerate(ev_pk):
                for ps in ev_ps:
                    pk_end = pk['endtime'] if 'endtime' in pk.dtype.names else pk['time'] + pk['length'] * pk['dt']
                    ps_end = ps['endtime'] if 'endtime' in ps.dtype.names else ps['time'] + ps['length'] * ps['dt'] if 'length' in ps.dtype.names else ps['endtime']
                    if ps['time'] <= pk['time'] and ps_end >= pk_end:
                        pk_x[j] = ps['x_cnn'] if 'x_cnn' in ps.dtype.names else (ps['x'] if 'x' in ps.dtype.names else np.nan)
                        pk_y[j] = ps['y_cnn'] if 'y_cnn' in ps.dtype.names else (ps['y'] if 'y' in ps.dtype.names else np.nan)
                        break
        pos_list.append(np.column_stack([pk_x, pk_y]))

        eac_list.append(eac[fci_ec == i][0] if eac is not None and fci_ec is not None and np.any(fci_ec == i) else None)

    # Build bundle
    bundle = {
        'events': sel,
        'peaks_list': np.array(peaks_list, dtype=object),
        'peak_positions': np.array(pos_list, dtype=object),
        'event_numbers': np.array([int(e['event_number']) for e in sel]),
        'pmt_x': pmt_pos['x'], 'pmt_y': pmt_pos['y'],
        'pmt_array': pmt_pos['array'].astype(str), 'pmt_i': pmt_pos['i'],
        'to_pe': to_pe, 'run_id': run_id,
        'waveform_source': 'real_data' if is_real_data else 'model',
    }
    if any(e is not None for e in eac_list):
        bundle['eac_list'] = np.array(eac_list, dtype=object)

    out = os.path.join(output_dir, f'events_{run_id}_bundle.npz')
    np.savez_compressed(out, **bundle)
    print(f'-> {out} ({os.path.getsize(out)/1024:.0f} KB)')
    print(f'   Events: {len(sel)}, Real data: {is_real_data}, Positions: {positions is not None}')
    return out


def main():
    p = argparse.ArgumentParser(description='Unified XENONnT NPZ extraction')
    p.add_argument('--run', help='Single run ID')
    p.add_argument('--batch', help='Comma-separated run IDs for batch extraction')
    p.add_argument('--n', type=int, default=50, help='Events per run')
    p.add_argument('--s1-min', type=float, default=500)
    p.add_argument('--s2-min', type=float, default=50000)
    p.add_argument('--output-dir', default='.')
    args = p.parse_args()

    runs = []
    if args.run:
        runs = [args.run]
    elif args.batch:
        runs = [r.strip() for r in args.batch.split(',')]
    else:
        print('Please specify --run or --batch')
        return

    for run_id in runs:
        try:
            extract_run(run_id, args.n, args.s1_min, args.s2_min, args.output_dir)
        except Exception as e:
            print(f'ERROR on run {run_id}: {e}')

    print('\nDone.')


if __name__ == '__main__':
    main()
