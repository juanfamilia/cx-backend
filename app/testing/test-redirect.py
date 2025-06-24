import httpx
import asyncio


def get_video_url_download(uid: str) -> str:
    return f"https://customer-hmba8ctlrczwxylv.cloudflarestream.com/{uid}/downloads/default.mp4"


async def resolve_video_url(uid: str) -> str:
    url = get_video_url_download(uid)

    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        try:
            # HEAD evita descargar el archivo, pero sigue redirecciones
            response = await client.head(url, follow_redirects=True)
            final_url = str(response.url)

            # Verifica que haya sido redirigido
            if str(response.url) == url:
                print(
                    "No se pudo resolver la URL del video, la URL final es la misma que la original."
                )

            return final_url

        except httpx.HTTPError as e:
            print("Error al resolver URL del video: %s", str(e))


if __name__ == "__main__":
    result = asyncio.run(resolve_video_url("bbeabe214c2ac4c74a2d7d618ae53f56"))
    print("URL resuelta:", result)
