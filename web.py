
import re
import shutil
import sys
from io import BytesIO
from urllib.parse import urljoin, urlparse

import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


st.set_page_config(
    page_title="Amazon Web Scraping",
    page_icon="🛒",
    layout="wide"
)

st.title(" Amazon Web Scraping")
st.write(
    "Busca productos de Amazon y extrae información "
    "con Selenium y Pandas."
)

COLUMNAS = [
    "ASIN",
    "Producto",
    "Precio",
    "Calificación",
    "Enlace"
]

if "driver" not in st.session_state:
    st.session_state.driver = None

if "productos" not in st.session_state:
    st.session_state.productos = pd.DataFrame(
        columns=COLUMNAS
    )


# CONFIGURAR CHROME
def crear_navegador():

    opciones = webdriver.ChromeOptions()
    opciones.add_argument("--window-size=1400,1000")

    if sys.platform.startswith("linux"):

        opciones.add_argument("--headless=new")
        opciones.add_argument("--no-sandbox")
        opciones.add_argument("--disable-dev-shm-usage")

        chrome = (
            shutil.which("chromium")
            or shutil.which("chromium-browser")
            or shutil.which("google-chrome")
        )

        chromedriver = shutil.which("chromedriver")

        if not chrome or not chromedriver:
            raise RuntimeError(
                "No se encontró Chromium o ChromeDriver. "
                "Revisa packages.txt."
            )

        opciones.binary_location = chrome

        return webdriver.Chrome(
            service=Service(
                executable_path=chromedriver
            ),
            options=opciones
        )

    return webdriver.Chrome(options=opciones)


# VALIDAR URL
def es_url_amazon(url):

    datos = urlparse(url)
    host = (datos.hostname or "").lower()

    return datos.scheme in ("http", "https") and (
        host == "amazon.com.mx"
        or host.endswith(".amazon.com.mx")
    )


# EXTRAER PRODUCTOS
def extraer_productos(html, url_actual):

    sopa = BeautifulSoup(html, "html.parser")

    titulo_pagina = (
        sopa.title.get_text(" ", strip=True).lower()
        if sopa.title
        else ""
    )

    if (
        "validatecaptcha" in html.lower()
        or "robot check" in titulo_pagina
    ):
        return None

    productos = []
    vistos = set()

    tarjetas = sopa.select(
        'div[data-component-type="s-search-result"][data-asin]'
    )

    for tarjeta in tarjetas:

        asin = tarjeta.get("data-asin", "").strip()

        if not asin or asin in vistos:
            continue

        titulo = tarjeta.select_one("h2 span")
        enlace = tarjeta.select_one("h2 a[href]")

        if not titulo:
            continue

        precio = tarjeta.select_one(
            ".a-price .a-offscreen"
        )

        calificacion = tarjeta.select_one(
            ".a-icon-alt"
        )

        if enlace:
            enlace_producto = urljoin(
                "https://www.amazon.com.mx",
                enlace.get("href", "")
            )
        else:
            enlace_producto = (
                f"https://www.amazon.com.mx/dp/{asin}"
            )

        productos.append({
            "ASIN": asin,
            "Producto": titulo.get_text(
                " ", strip=True
            ),
            "Precio": (
                precio.get_text(" ", strip=True)
                if precio
                else "No disponible"
            ),
            "Calificación": (
                calificacion.get_text(" ", strip=True)
                if calificacion
                else "No disponible"
            ),
            "Enlace": enlace_producto
        })

        vistos.add(asin)

    # EXTRAER PRODUCTO INDIVIDUAL
    if not productos:

        titulo = sopa.select_one("#productTitle")

        if titulo:

            coincidencia = re.search(
                r"/dp/([A-Z0-9]{10})",
                url_actual,
                re.I
            )

            asin = (
                coincidencia.group(1).upper()
                if coincidencia
                else "No disponible"
            )

            precio = (
                sopa.select_one(
                    "#corePrice_feature_div .a-offscreen"
                )
                or sopa.select_one(
                    ".a-price .a-offscreen"
                )
            )

            calificacion = sopa.select_one(
                "#acrPopover .a-icon-alt"
            )

            productos.append({
                "ASIN": asin,
                "Producto": titulo.get_text(
                    " ", strip=True
                ),
                "Precio": (
                    precio.get_text(" ", strip=True)
                    if precio
                    else "No disponible"
                ),
                "Calificación": (
                    calificacion.get_text(" ", strip=True)
                    if calificacion
                    else "No disponible"
                ),
                "Enlace": url_actual
            })

    return pd.DataFrame(
        productos,
        columns=COLUMNAS
    )


# GENERAR EXCEL
def crear_excel(df):

    archivo = BytesIO()

    with pd.ExcelWriter(
        archivo,
        engine="openpyxl"
    ) as escritor:

        df.to_excel(
            escritor,
            sheet_name="Productos Amazon",
            index=False
        )

    return archivo.getvalue()


# INTERFAZ STREAMLIT
url = st.text_input(
    "Enlace de Amazon México:",
    value="https://www.amazon.com.mx/s?k=lego+snoopy"
)

col1, col2, col3 = st.columns(3)

with col1:
    abrir = st.button(
        "🌐 Abrir Amazon",
        use_container_width=True
    )

with col2:
    extraer = st.button(
        "🔎 Extraer productos",
        use_container_width=True
    )

with col3:
    cerrar = st.button(
        "❌ Cerrar navegador",
        use_container_width=True
    )


# ABRIR AMAZON
if abrir:

    if not es_url_amazon(url):

        st.error(
            "Ingresa una URL válida de amazon.com.mx"
        )

    else:

        try:

            if st.session_state.driver is not None:

                try:
                    st.session_state.driver.quit()
                except Exception:
                    pass

                st.session_state.driver = None

            navegador = crear_navegador()

            st.session_state.driver = navegador

            navegador.get(url)

            st.session_state.productos = (
                pd.DataFrame(columns=COLUMNAS)
            )

            st.success(
                "Amazon se abrió correctamente."
            )

            if sys.platform.startswith("linux"):

                st.info(
                    "En Streamlit Cloud Chrome funciona "
                    "sin ventana visible. Si Amazon pide "
                    "CAPTCHA, no podrás resolverlo desde "
                    "esta aplicación."
                )

            else:

                st.info(
                    "Si aparece un CAPTCHA, resuélvelo "
                    "en Chrome. Después regresa y pulsa "
                    "'Extraer productos'."
                )

        except Exception as error:

            st.error(
                f"Error al abrir Chrome: {error}"
            )


# EXTRAER INFORMACIÓN
if extraer:

    navegador = st.session_state.driver

    if navegador is None:

        st.warning(
            "Primero haz clic en 'Abrir Amazon'."
        )

    else:

        try:

            productos = extraer_productos(
                navegador.page_source,
                navegador.current_url
            )

            if productos is None:

                st.error(
                    "Amazon mostró un CAPTCHA. "
                    "En tu Mac puedes resolverlo "
                    "manualmente; en Streamlit Cloud "
                    "el navegador es invisible."
                )

            elif productos.empty:

                st.warning(
                    "No se encontraron productos. "
                    "Comprueba la página abierta. "
                    "Amazon puede cambiar su estructura "
                    "o restringir el acceso automatizado."
                )

            else:

                st.session_state.productos = productos

                st.success(
                    f"Se extrajeron {len(productos)} productos."
                )

        except Exception as error:

            st.error(
                f"Error al extraer los productos: {error}"
            )


# CERRAR NAVEGADOR
if cerrar:

    navegador = st.session_state.driver

    if navegador is not None:

        try:
            navegador.quit()
        except Exception:
            pass

    st.session_state.driver = None

    st.info("Navegador cerrado.")


# MOSTRAR RESULTADOS
if not st.session_state.productos.empty:

    st.subheader("📦 Productos encontrados")

    st.dataframe(
        st.session_state.productos,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        label="📥 Descargar resultados en Excel",
        data=crear_excel(
            st.session_state.productos
        ),
        file_name="productos_amazon.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )



