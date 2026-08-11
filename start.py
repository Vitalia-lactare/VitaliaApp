import socket
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

PORT = 8000


def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # nao envia trafego de fato, so resolve a rota local
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def print_access_info(lan_ip: str) -> None:
    local_url = f"http://127.0.0.1:{PORT}"
    lan_url = f"http://{lan_ip}:{PORT}"

    print("=" * 60)
    print(" Vitalia — servidor iniciado")
    print("=" * 60)
    print(f" Neste computador : {local_url}")
    print(f" No celular (Wi-Fi): {lan_url}")
    print(" Abra o link do celular no navegador e use")
    print(' "Adicionar a tela inicial" para instalar o atalho.')
    print("=" * 60)

    try:
        import qrcode

        qr = qrcode.QRCode(border=1)
        qr.add_data(lan_url)
        qr.make()
        qr.print_ascii(invert=True)
    except ImportError:
        print(" (dica: instale 'qrcode[pil]' para ver um QR code aqui)")


def main() -> None:
    import uvicorn

    lan_ip = get_lan_ip()
    print_access_info(lan_ip)
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=False)


if __name__ == "__main__":
    main()
