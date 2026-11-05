
import sys
import shutil
import re
import streamlit as st
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from urllib.parse import urljoin

st.title("Amazon Web Scraping")
st.write("Extrae productos de Amazon con Selenium y Pandas")

# Convertir los precios de texto a números
def convertir_precio(texto):
    if not texto or texto == "No disponible":
        return None

    limpio = re.sub(r"[^\d,.]", "", texto)

    if not limpio:
        return None

    try:
        if "," in limpio and "." in limpio:
            if limpio.rfind(".") > limpio.rfind(","):
                limpio = limpio.replace(",", "")
            else:
                limpio = limpio.replace(".", "")
                limpio = limpio.replace(",", ".")

        elif "," in limpio:
            partes = limpio.split(",")
            if len(partes[-1]) == 3:
                limpio = limpio.replace(",", "")
            else:
                limpio = limpio.replace(",", ".")

        elif "." in limpio:
            partes = limpio.split(".")
            if len(partes[-1]) == 3:
                limpio = limpio.replace(".", "")

        return float(limpio)

    except ValueError:
        return None


url = st.text_input(
    "Enlace de búsqueda:",
    "https://www.amazon.com.mx/s?k=lego+snoopy"
)

# Guardar el navegador durante la sesión
if "driver" not in st.session_state:
    st.session_state.driver = None

# Guardar los productos encontrados
if "productos" not in st.session_state:
    st.session_state.productos = None


# Abrir Amazon
if st.button("🌐 Abrir Amazon"):

    try:
        if st.session_state.driver is not None:
            st.session_state.driver.quit()
            st.session_state.driver = None

        st.session_state.productos = None

        # Configurar Chrome para Streamlit Cloud
        # o para ejecutarlo en tu MacBook
        if sys.platform.startswith("linux"):
            opciones = webdriver.ChromeOptions()
            opciones.add_argument("--headless=new")
            opciones.add_argument("--no-sandbox")
            opciones.add_argument("--disable-dev-shm-usage")

            ruta_chrome = (
                shutil.which("chromium")
                or shutil.which("chromium-browser")
                or shutil.which("google-chrome")
            )

            ruta_driver = shutil.which("chromedriver")

            if not ruta_chrome or not ruta_driver:
                raise RuntimeError(
                    "No se encontró Chromium o ChromeDriver. "
                    "Revisa packages.txt en GitHub."
                )

            opciones.binary_location = ruta_chrome

            driver = webdriver.Chrome(
                service=Service(ruta_driver),
                options=opciones
            )

        else:
            driver = webdriver.Chrome()

        driver.get(url)

        st.session_state.driver = driver

        st.success("Amazon abierto en Chrome")

        if sys.platform.startswith("linux"):
            st.info(
                "Chrome se está ejecutando en el servidor, "
                "sin ventana visible. Si Amazon solicita un "
                "CAPTCHA, no podrás resolverlo manualmente "
                "en Streamlit Cloud."
            )
        else:
            st.info(
                "Si aparece un CAPTCHA, resuélvelo "
                "manualmente. Después abre la página "
                "de resultados y regresa a Streamlit."
            )

    except Exception as e:
        st.error(f"Error al abrir Chrome: {e}")


# Extraer productos
if st.button("🔍 Extraer productos"):

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

                precio_texto = (
                    precio.get_text(strip=True)
                    if precio else "No disponible"
                )

                producto = {
                    "Producto": titulo.get_text(
                        strip=True
                    ),
                    "Precio": precio_texto,
                    "Precio (MXN)": convertir_precio(
                        precio_texto
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

                st.session_state.productos = df

                st.success(
                    f"Se encontraron {len(df)} productos"
                )

            else:
                st.session_state.productos = None

                st.warning(
                    "No se encontraron productos. "
                    "Comprueba que Chrome muestra "
                    "los resultados de búsqueda. "
                    "Amazon también podría haber "
                    "bloqueado Selenium."
                )

        except Exception as e:
            st.error(
                f"Error durante la extracción: {e}"
            )


# NUEVA FUNCIÓN: FILTRAR POR PRECIO
if st.session_state.productos is not None:

    df = st.session_state.productos.copy()

    st.subheader("🛒 Filtrar productos por precio")

    st.write(
        "Selecciona el precio mínimo y máximo "
        "de los productos que deseas visualizar."
    )

    precios_validos = df["Precio (MXN)"].dropna()

    if not precios_validos.empty:

        precio_maximo = float(precios_validos.max())

        col1, col2 = st.columns(2)

        with col1:
            minimo = st.number_input(
                "Precio mínimo ($ MXN)",
                min_value=0.0,
                value=0.0,
                step=50.0
            )

        with col2:
            maximo = st.number_input(
                "Precio máximo ($ MXN)",
                min_value=0.0,
                value=precio_maximo,
                step=50.0
            )

        orden = st.selectbox(
            "Ordenar productos por:",
            [
                "Sin ordenar",
                "Precio: menor a mayor",
                "Precio: mayor a menor"
            ]
        )

        if minimo > maximo:
            st.error(
                "El precio mínimo no puede ser "
                "mayor que el precio máximo."
            )

        else:
            # Aplicar filtro
            df_filtrado = df[
                (df["Precio (MXN)"] >= minimo)
                &
                (df["Precio (MXN)"] <= maximo)
            ].copy()

            # Ordenar resultados
            if orden == "Precio: menor a mayor":
                df_filtrado = df_filtrado.sort_values(
                    by="Precio (MXN)",
                    ascending=True
                )

            elif orden == "Precio: mayor a menor":
                df_filtrado = df_filtrado.sort_values(
                    by="Precio (MXN)",
                    ascending=False
                )

            st.subheader("📊 Resultados filtrados")

            st.write(
                f"Se encontraron {len(df_filtrado)} "
                "productos dentro del rango seleccionado."
            )

            if not df_filtrado.empty:

                st.dataframe(
                    df_filtrado,
                    use_container_width=True,
                    hide_index=True
                )

                csv = df_filtrado.to_csv(
                    index=False
                ).encode("utf-8-sig")

                st.download_button(
                    "📥 Descargar productos filtrados",
                    csv,
                    "productos_amazon_filtrados.csv",
                    "text/csv"
                )

            else:
                st.warning(
                    "No hay productos dentro "
                    "del rango de precios seleccionado."
                )

        sin_precio = df["Precio (MXN)"].isna().sum()

        if sin_precio > 0:
            st.caption(
                f"{sin_precio} productos no tienen "
                "un precio disponible y se excluyen "
                "del filtro."
            )

    else:
        st.warning(
            "No se encontraron precios válidos "
            "para aplicar el filtro."
        )
        st.dataframe(df)

