# Radio transcription

Listens to the department's fire channel with an RTL-SDR USB receiver, transcribes each
transmission with Whisper, and posts the text to the app's Live Radio page
(`/api/radio/transcription`).

Spring Valley VFD "COM 2": **155.400 MHz, analog FM, 100.0 Hz PL**.

## Hardware
- RTL-SDR Blog V4 dongle
- VHF antenna (136–174 MHz) in a window
- Any always-on Mac or Linux box (ours is a 2015 Intel MacBook Air)

## Install (macOS)
```bash
brew install librtlsdr          # provides rtl_fm and rtl_power
pip3 install --user numpy scipy faster-whisper sounddevice
```
Copy `radio_transcribe.py` to the machine, then run it, or install the LaunchAgent
(`com.svvfd.radio.plist`; edit the script path inside it) so it starts at login and restarts if it crashes:
```bash
cp com.svvfd.radio.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.svvfd.radio.plist
```

## Files on the receiving machine
| File | Purpose |
|------|---------|
| `~/radio_freq.txt` | Frequency to listen on (e.g. `155.400M`) |
| `~/radio_no_mic` | If present, the microphone tone-finder is off (normal now the channel is known) |
| `~/radio_no_sdr` | If present, the dongle is left free (e.g. for `rf_activity_logger.py`) |
| `~/radio_captures/` | Last 300 recordings, for checking transcription quality |
| `~/radio_transcribe_v5.log` | Log (path set in the plist) |

## Settings that matter
- **Gain 40.** At 49.6 the dongle overloads on 155.400 and static reads as a signal, so recordings never end.
- **Noise squelch:** a transmission is "on" when the hiss above 4 kHz drops (FM quieting), not when the audio gets louder.

## Finding an unknown channel
`rf_activity_logger.py 136M:174M 5k` logs the time and frequency of every transmission across the band.
Note when your radio goes off and match the times — that is how COM 2 was found.
