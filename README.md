![IDRB banner](https://github.com/damp11113/IDRB/assets/64675096/b874d876-139d-4236-a31b-ae5ddb8b82fd)

# IDRB (Internet Digital Radio Broadcasting) System
IDRB is a novel internet radio broadcasting alternative that uses HLS/DASH/HTTP streams, transferring over TCP/IP. This system supports images and RDS (Dynamic update) capabilities, enabling the transmission of station information. Additionally, it allows for setting station logos and images. IDRB offers multi-broadcasting functionalities and currently supports the Opus codec, with plans to incorporate PCM, MP2/3, AAC/AAC+, and more in the future, ensuring low delay. If you find this project intriguing.

# Previews
![preview](https://github.com/damp11113/IDRB/assets/64675096/ec423b0d-3598-49f3-89bb-8170e9c89563)
### Server Selector
![Recording 2024-02-26 200657](https://github.com/damp11113/IDRB/assets/64675096/5bd68eb0-0306-4fbf-86fd-0b3124736fa8)


# Fetures
- [x] Encryption (Beta)
- [x] Low Latency
- [x] MultiChannel on one server
- [x] Low bandwidth using
- [x] [RDS](https://en.wikipedia.org/wiki/Radio_Data_System) but in **internet** (Dynamic updating)
- [x] Images (Logo only) (on RDS)
- [ ] [EPG](https://en.wikipedia.org/wiki/Electronic_program_guide) (on RDS)
- [ ] AS (Alternative Server) (on RDS)
- [ ] [EOM](https://en.wikipedia.org/wiki/Enhanced_other_networks) (on RDS)


## Protocol
- [x] TCP
- [x] ZeroMQ
- [x] ZeroMQ (WebSocket)
- [ ] UDP
- [ ] WebSocket
- [ ] Socketio
- [ ] HTTP/HTTPS (not IDRB system, for http broadcast only)

## Audio codec
- [x] Opus
- [x] PCM (Raw Audio)
- [ ] MP3 (In Devlopment)
- [ ] Vorbis
- [ ] AAC/AAC+ (XHE-AAC)
- [ ] Flac
- [ ] Codec2 (For Voice only)

### Audio channel
- [x] Mono
- [x] Stereo
- [ ] 5.1/7.1 surround (opus/pcm)
- [ ] Dolby Atmos 
