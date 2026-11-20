import os
import sys
import ssl
import http.server
import socketserver
from pathlib import Path

PORT = 3000
DIRECTORY = Path(__file__).resolve().parent

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def generate_self_signed_cert(cert_file: Path, key_file: Path):
    """Gera certificado SSL autoassinado temporário usando Python puro ou openssl se disponível."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName("localhost"), x509.IPAddress(bytes([127, 0, 0, 1]))]),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )

        with open(key_file, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        return True
    except Exception:
        return False

def main():
    cert_file = DIRECTORY / "localhost.crt"
    key_file = DIRECTORY / "localhost.key"

    use_https = False
    if not (cert_file.exists() and key_file.exists()):
        generate_self_signed_cert(cert_file, key_file)

    server_address = ("127.0.0.1", PORT)
    httpd = socketserver.TCPServer(server_address, CORSRequestHandler)

    if cert_file.exists() and key_file.exists():
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=str(cert_file), keyfile=str(key_file))
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            use_https = True
        except Exception as e:
            print(f"Aviso: Não foi possível habilitar SSL ({e}). Iniciando via HTTP padrão.")
            use_https = False

    protocol = "https" if use_https else "http"
    print("\n" + "=" * 65)
    print("🚀 Organizer App — Servidor Local do Suplemento Excel (RF-10)")
    print("=" * 65)
    print(f"• URL do Taskpane:   {protocol}://localhost:{PORT}/src/taskpane.html")
    print(f"• URL do Manifesto:  {protocol}://localhost:{PORT}/manifest.xml")
    print(f"• Diretório raiz:    {DIRECTORY}")
    print("=" * 65)
    print("Pressione Ctrl+C para encerrar o servidor.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado com sucesso.")

if __name__ == "__main__":
    main()
