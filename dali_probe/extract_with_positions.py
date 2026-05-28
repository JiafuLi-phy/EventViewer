#!/usr/bin/env python3
"""Extract NPZ bundle from Midway3/DALI including per-peak CNN positions."""
import argparse, os, sys, json, warnings, numpy as np
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from event_plotter import io

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run', default='023756')
    p.add_argument('--n', type=int, default=50)
    p.add_argument('--s1-min', type=float, default=500)
    p.add_argument('--s2-min', type=float, default=50000)
    p.add_argument('--output', default='')
    args = p.parse_args()

    run_id = args.run
    print(f'Loading run {run_id}...')

    events = io.load_strax_chunks(run_id, 'event_info')
    pmt_pos = io.load_pmt_geometry()
    to_pe = io.load_to_pe(n_channels=len(pmt_pos))

    # Select events
    mask = np.ones(len(events), dtype=bool)
    if 's1_area' in events.dtype.names:
        mask &= events['s1_area'] > args.s1_min
    if 's2_area' in events.dtype.names:
        mask &= events['s2_area'] > args.s2_min
    sel = events[mask]
    sel = sel[np.argsort(sel['s2_area'])[::-1][:args.n]]
    sel = sel[np.argsort(sel['time'])]
    print(f'Selected {len(sel)} events')

    # Load peaks and positions
    peaks_all = io.load_strax_chunks(run_id, 'peak_basics')
    print(f'Loaded {len(peaks_all)} peaks')

    pos_data = None
    pos_dir = io.find_data_dir(run_id, 'peak_positions_cnn')
    if pos_dir:
        pos_data = io.load_strax_chunks(run_id, 'peak_positions_cnn')
        print(f'Loaded {len(pos_data)} CNN positions')

    eac_all = None
    eac_dir = io.find_data_dir(run_id, 'event_area_per_channel')
    if eac_dir:
        eac_all = io.load_strax_chunks(run_id, 'event_area_per_channel')
        print(f'Loaded EAC data')

    import strax
    fci_pk = strax.fully_contained_in(peaks_all, sel)
    fci_ps = strax.fully_contained_in(pos_data, sel) if pos_data is not None else None
    fci_ec = strax.fully_contained_in(eac_all, sel) if eac_all is not None else None

    peaks_list, eac_list, pos_list = [], [], []

    for i in range(len(sel)):
        ev = sel[i]
        ev_pk = peaks_all[fci_pk == i]
        peaks_list.append(ev_pk)

        # Match positions to peaks by time
        pk_x = np.full(len(ev_pk), np.nan)
        pk_y = np.full(len(ev_pk), np.nan)
        if pos_data is not None and fci_ps is not None:
            ev_pos = pos_data[fci_ps == i]
            for j, pk in enumerate(ev_pk):
                for ps in ev_pos:
                    if ps['time'] <= pk['time'] and ps['endtime'] >= pk['endtime']:
                        pk_x[j] = ps['x_cnn']
                        pk_y[j] = ps['y_cnn']
                        break
        pos_list.append(np.column_stack([pk_x, pk_y]))

        if eac_all is not None and fci_ec is not None:
            idx = np.where(fci_ec == i)[0]
            eac_list.append(eac_all[idx[0]] if len(idx) else None)
        else:
            eac_list.append(None)

    # Build bundle
    bundle = {
        'events': sel,
        'peaks_list': np.array(peaks_list, dtype=object),
        'peak_positions': np.array(pos_list, dtype=object),
        'event_numbers': np.array([int(e['event_number']) for e in sel], dtype=np.int32),
        'pmt_x': pmt_pos['x'], 'pmt_y': pmt_pos['y'],
        'pmt_array': pmt_pos['array'].astype(str), 'pmt_i': pmt_pos['i'],
        'to_pe': to_pe, 'run_id': run_id,
        'waveform_source': 'model_with_positions',
    }
    if any(e is not None for e in eac_list):
        bundle['eac_list'] = np.array(eac_list, dtype=object)

    out = args.output or f'events_{run_id}_with_positions.npz'
    np.savez_compressed(out, **bundle)
    print(f'Saved {len(sel)} events to {out} ({os.path.getsize(out)/1024:.0f} KB)')

if __name__ == '__main__':
    main()
