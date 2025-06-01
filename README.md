# Tubes1_9ame-9acor
## 1.Penjelasan Algoritma Greedy Yang Diimplementasikan
Algoritma Greedy yang diimplementasikan mencakup:
1) Mencari diamond terdekat, jika diamond merah dan diamond biru berada pada jarak yang sama maka akan memprioritaskan diamond dengan value yang lebih tinggi
2) Mencari tombol merah untuk melakukan reset pada posisi dan diamonds jika tombol merah lebih dekat dibandingkan diamond
3) Mencari diamond yang berada di sekitar base, wilayah pencarian diamond di sekitar base menjadi prioritas utama
4) Bot akan kembali ke base apabila inventory bot telah penuh dan bot tidak menemukan diamond yang dekat dengan base ketika perjalanan pulang

## 2. Requirements tertentu
Program membutuhkan requirements sebagai berikut agar dapat dijalankan dengan baik:
- NodeJS (npm)
- Yarn
- Docker 

## 3. Langkah-langkah mengcompile atau build program
1. Clone repository ini sebagai logic bot yang akan digunakan
   `git clone https://github.com/7H0shi/Tubes1_9ame-9acor.git`

2. Clone repository ini sebagai game engine etimo 1.1
   `git clone https://github.com/haziqam/tubes1-IF2211-game-engine/releases/tag/v1.1.0`

3. Jalankan bot dengan run-bots.bat atau run-bots.sh
   
4. Menjalankan bot secara keseluruhan dengan
   `./run-bots.bat`
   atau
   `chmod +x ./run-bots.sh
   ./run-bots.sh`
   
5. Jalankan bot secara manual
   Menggunakan command
   `python main.py --logic gacorbot --email=9ame_9acor@gmail.com --name=gacorbot --password=123456 --team etimo`
