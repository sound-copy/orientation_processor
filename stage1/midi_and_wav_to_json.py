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
    print(f"Attempting to analyze WAV: {wavpath}") # DEBUG
    if not wavpath.exists():
        print(f"WAV file does not exist at analyse_wav: {wavpath}") # DEBUG
        return {} # Or raise error
    try:
        dur = librosa.get_duration(path=wavpath)
        y, sr = sf.read(wavpath) # type: ignore
        rms = float((y ** 2).mean() ** 0.5) # type: ignore
        print(f"WAV analysis successful: duration={dur}, rms={rms}") # DEBUG
        return {"duration_sec": dur, "rms": rms}
    except Exception as e:
        print(f"Error during WAV analysis for {wavpath}: {e}", file=sys.stderr) # DEBUG
        return {}


def build_json(meta, midi, wav=None) -> dict:
    out = {"meta": meta, "midi": midi}
    if wav and wav.get("duration_sec") is not None: # Check if wav actually has data
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
        
    print(f"--- Debug Info ---")
    print(f"Script directory: {script_dir}")
    print(f"Current Working Dir: {pathlib.Path.cwd()}")
    print(f"Config file used: {config_path}")
    print(f"Config 'input_dir': {cfg['input_dir']}")
    print(f"Resolved input directory (in_dir): {in_dir}")
    print(f"Config 'output_dir': {cfg['output_dir']}")
    print(f"Resolved output directory (out_dir): {out_dir}")
    print(f"WAV analysis enabled in config: {cfg['wav_analysis']}")
    print(f"--- End Debug Info ---")

    for mid in sorted(in_dir.glob('*.mid')):
        print(f"\nProcessing MIDI file: {mid.name} (full path: {mid})")
        meta = parse_filename(mid)
        midi_data = extract_midi(mid)
        
        wav_match = mid.with_suffix('.wav')
        print(f"Expected WAV file path: {wav_match}") # DEBUG
        
        wav_data = None # Initialize wav_data
        if cfg['wav_analysis']:
            print(f"WAV analysis is enabled.") # DEBUG
            if wav_match.exists():
                print(f"Matching WAV file found: {wav_match.name}") # DEBUG
                try:
                    wav_data = analyse_wav(wav_match)
                    if not wav_data: # If analyse_wav returned empty dict due to error
                         print(f"WAV analysis for {wav_match.name} did not produce data.")
                except Exception as e:
                    print(f"Error calling analyse_wav for {wav_match}: {e}", file=sys.stderr)
            else:
                print(f"Matching WAV file NOT found at: {wav_match}") # DEBUG
        else:
            print(f"WAV analysis is disabled in config.") # DEBUG

        data = build_json(meta, midi_data, wav_data)
        save_json(data, out_dir)
        
        title_str = str(data['meta']['title']) if data['meta']['title'] is not None else "untitled"
        ordinal_str = str(data['meta']['ordinal']) + "-" if data['meta']['ordinal'] is not None else ""
        json_filename = f"{ordinal_str}{title_str}.json"
        print(f"✓ {mid.name} → {out_dir / json_filename}")

if __name__ == '__main__':
    main()