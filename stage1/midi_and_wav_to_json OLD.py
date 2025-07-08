#!/usr/bin/env python
import argparse
import json
import sys
import yaml
import pathlib
from mido import MidiFile # type: ignore
import soundfile as sf # type: ignore
import librosa # type: ignore

def parse_filename(p: pathlib.Path) -> dict:
    stem = p.stem
    parts = stem.split('-')
    return {
        "ordinal": int(parts[0]) if parts[0].isdigit() else None,
        "title": parts[1] if len(parts) > 1 else stem,
    }

def extract_midi(midipath: pathlib.Path) -> dict:
    mf = MidiFile(midipath)
    notes = []
    abs_time = 0
    for msg in mf:
        abs_time += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            notes.append({"note": msg.note, "t": abs_time})
    return {
        "ticks_per_beat": mf.ticks_per_beat,
        "tempo": None,                # will fill later
        "notes": notes,
    }

def analyse_wav(wavpath: pathlib.Path) -> dict:
    dur = librosa.get_duration(path=wavpath)
    y, sr = sf.read(wavpath) # type: ignore
    rms = float((y ** 2).mean() ** 0.5) # type: ignore
    return {"duration_sec": dur, "rms": rms}

def build_json(meta, midi, wav=None) -> dict:
    out = {"meta": meta, "midi": midi}
    if wav:
        out["audio"] = wav
    return out

def save_json(data, outdir: pathlib.Path):
    outdir.mkdir(parents=True, exist_ok=True)
    title_str = str(data['meta']['title']) if data['meta']['title'] is not None else "untitled"
    ordinal_str = str(data['meta']['ordinal']) + "-" if data['meta']['ordinal'] is not None else ""
    name = f"{ordinal_str}{title_str}.json"
    (outdir / name).write_text(json.dumps(data, indent=2))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cfg', default='config_stage1.yaml', help="Path to the configuration file (relative to the script's directory if not absolute)")
    ap.add_argument('--interactive', action='store_true')
    args = ap.parse_args()

    script_dir = pathlib.Path(__file__).parent.resolve()
    
    config_path_str = args.cfg
    if not pathlib.Path(config_path_str).is_absolute():
        config_path = script_dir / config_path_str
    else:
        config_path = pathlib.Path(config_path_str)

    cfg = yaml.safe_load(open(config_path))
    
    in_dir_str = cfg['input_dir']
    if not pathlib.Path(in_dir_str).is_absolute():
        in_dir = (script_dir / in_dir_str).resolve()
    else:
        in_dir = pathlib.Path(in_dir_str).expanduser().resolve()

    out_dir_str = cfg['output_dir']
    if not pathlib.Path(out_dir_str).is_absolute():
        out_dir = (script_dir / out_dir_str).resolve()
    else:
        out_dir = pathlib.Path(out_dir_str).expanduser().resolve()
        
    print(f"Script directory: {script_dir}")
    print(f"Input directory: {in_dir}")
    print(f"Output directory: {out_dir}")
    print(f"Config file used: {config_path}")

    for mid in sorted(in_dir.glob('*.mid')):
        print(f"Processing {mid.name}...")
        meta = parse_filename(mid)
        midi_data = extract_midi(mid)
        wav_match = mid.with_suffix('.wav')
        wav_data = None
        if cfg['wav_analysis'] and wav_match.exists():
            try:
                wav_data = analyse_wav(wav_match)
            except Exception as e:
                print(f"Warning: Could not analyze WAV file {wav_match}: {e}", file=sys.stderr)

        data = build_json(meta, midi_data, wav_data)
        save_json(data, out_dir)
        # Construct the expected output filename for the print statement
        title_str = str(data['meta']['title']) if data['meta']['title'] is not None else "untitled"
        ordinal_str = str(data['meta']['ordinal']) + "-" if data['meta']['ordinal'] is not None else ""
        json_filename = f"{ordinal_str}{title_str}.json"
        print(f"✓ {mid.name} → {out_dir / json_filename}")


if __name__ == '__main__':
    main()
