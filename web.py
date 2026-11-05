
import streamlit as st
import pandas as pd

from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import urljoin

st.title("Amazon Web Scraping")
st.write("Extrae productos de Amazon con Selenium y Pandas")

url = st.text_input(
    "Enlace de búsqueda:",
    "https://www.amazon.com.mx/s?k=lego+snoopy"
)

# Guardar el navegador durante la sesión
if "driver" not in st.session_state:
    st.session_state.driver = None

# Abrir Amazon
if st.button("🌐 Abrir Amazon"):

    try:
        if st.session_state.driver is not None:
            st.session_state.driver.quit()

        driver = webdriver.Chrome()
        driver.get(url)

        st.session_state.driver = driver

        st.success("Amazon abierto en Chrome")
        st.info(
            "Si aparece un CAPTCHA, resuélvelo "
            "manualmente. Después abre la página "
            "de resultados y regresa a Streamlit."
        )

    except Exception as e:
        st.error(f"Error al abrir Chrome: {e}")


# Extraer productos de la página abierta
if st.button(" Extraer productos"):

    driver = st.session_state.driver

    if driver is None:
        st.warning("Primero abre Amazon")

    else:
        try:
            html = driver.page_source

            soup = BeautifulSoup(
                html, "html.parser"
            )

            productos = []

            resultados = soup.select(
                '[data-component-type="s-search-result"]'
            )

            for item in resultados:

                titulo = item.select_one("h2 span")

                precio = item.select_one(
                    ".a-price .a-offscreen"
                )

                enlace = item.select_one("h2 a[href]")

                if titulo is None:
                    continue

                producto = {
                    "Producto": titulo.get_text(
                        strip=True
                    ),
                    "Precio": (
                        precio.get_text(strip=True)
                        if precio else "No disponible"
                    ),
                    "Enlace": (
                        urljoin(
                            "https://www.amazon.com.mx",
                            enlace.get("href")
                        )
                        if enlace else ""
                    )
                }

                productos.append(producto)

            if productos:

                df = pd.DataFrame(productos)

                st.success(
                    f"Se encontraron {len(df)} productos"
                )

                st.dataframe(df)

                csv = df.to_csv(
                    index=False
                ).encode("utf-8-sig")

                st.download_button(
                    "Descargar CSV",
                    csv,
                    "productos_amazon.csv",
                    "text/csv"
                )

            else:
                st.warning(
                    "No se encontraron productos. "
                    "Comprueba que Chrome muestra "
                    "los resultados de búsqueda. "
                    "Amazon también podría haber "
                    "bloqueado Selenium."
                )

        except Exception as e:
            st.error(f"Error durante la extracción: {e}")












