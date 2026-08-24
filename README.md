# EPMB x UTHM Exhibition Dashboard

This version replaces the old dashboard video section with a simpler VDO.Ninja viewer design and removes the manual inspection-entry workflow.

## What is included

- EPMB x UTHM logo at the top left
- Robot webcam viewer
- Creaform / inspection-software screen viewer
- Reconnect and Open buttons for both feeds
- Live feed state detection through the VDO.Ninja iframe API
- PASS / NG counts from `data/CF_Template_Latest.csv`
- Part-level result table
- Automatic CSV refresh every 10 seconds

## Run on the exhibition PC

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open:

`http://127.0.0.1:5000`

## Video setup

The dashboard expects these stream IDs by default:

- Robot: `uthehrobotcam2026`
- Software screen: `uthehcreaform2026`

A viewer URL is generated as:

`https://vdo.ninja/?view=STREAM_ID&autoplay&cleanoutput&cleanviewer&noaudio&codec=h264`

The publisher machines must actively publish into those exact stream IDs.

To change IDs without editing code:

```powershell
$env:ROBOT_STREAM_ID="your_robot_stream"
$env:SOFTWARE_STREAM_ID="your_software_stream"
python app.py
```

## Important

The dashboard cannot manufacture the camera feed. If a VDO.Ninja viewer opens but says **Waiting for stream**, the publisher page on the source PC/phone is not actively publishing that stream ID, or the source has disconnected.
