
import sys
import shutil
import re
import streamlit as st
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


# ==========================================
# 1. CONFIGURACIÓN DE LA APLICACIÓN
# ==========================================

st.set_page_config(
    page_title="Amazon Web Scraping",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 Amazon Web Scraping")

st.write(
    "Extrae productos de Amazon utilizando Python, "
    "Selenium, BeautifulSoup y Pandas."
)

st.write(
    "Consulta productos, compara precios, "
    "aplica filtros y descarga los resultados."
)


# ==========================================
# 2. CONVERTIR PRECIOS A NÚMEROS
# ==========================================

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


# ==========================================
# 3. CONFIGURAR SELENIUM
# ==========================================

def crear_navegador():

    if sys.platform.startswith("linux"):

        opciones = webdriver.ChromeOptions()

        opciones.add_argument("--headless=new")
        opciones.add_argument("--no-sandbox")
        opciones.add_argument("--disable-dev-shm-usage")
        opciones.add_argument("--window-size=1365,900")

        ruta_chrome = (
            shutil.which("chromium")
            or shutil.which("chromium-browser")
            or shutil.which("google-chrome")
        )

        ruta_driver = shutil.which("chromedriver")

        if not ruta_chrome or not ruta_driver:

            raise RuntimeError(
                "No se encontró Chromium o ChromeDriver. "
                "Revisa el archivo packages.txt."
            )

        opciones.binary_location = ruta_chrome

        driver = webdriver.Chrome(
            service=Service(ruta_driver),
            options=opciones
        )

    else:

        driver = webdriver.Chrome()

    driver.set_page_load_timeout(40)

    return driver


# ==========================================
# 4. GUARDAR DATOS DURANTE LA SESIÓN
# ==========================================

if "driver" not in st.session_state:
    st.session_state.driver = None

if "productos" not in st.session_state:
    st.session_state.productos = None


# ==========================================
# 5. INGRESAR ENLACE DE AMAZON
# ==========================================

st.subheader("🌐 Buscar productos")

url = st.text_input(
    "Introduce el enlace de búsqueda de Amazon:",
    "https://www.amazon.com.mx/s?k=lego+snoopy"
)


# ==========================================
# 6. ABRIR AMAZON
# ==========================================

if st.button("🌐 Abrir Amazon"):

    try:

        if st.session_state.driver is not None:

            try:
                st.session_state.driver.quit()
            except Exception:
                pass

            st.session_state.driver = None

        st.session_state.productos = None

        dominio = urlparse(url).hostname or ""

        if dominio not in (
            "amazon.com.mx",
            "www.amazon.com.mx"
        ):
            st.error(
                "Introduce un enlace válido "
                "de Amazon México."
            )

        else:

            with st.spinner("Abriendo Amazon..."):

                driver = crear_navegador()

                try:
                    driver.get(url)

                except Exception:
                    driver.quit()
                    raise

                st.session_state.driver = driver

            st.success("Amazon se abrió correctamente.")

            if sys.platform.startswith("linux"):

                st.info(
                    "Chrome funciona sin ventana visible "
                    "en Streamlit Cloud. Si Amazon muestra "
                    "un CAPTCHA o bloquea el acceso, "
                    "no será posible continuar con "
                    "la extracción desde esta sesión."
                )

            else:

                st.info(
                    "Chrome se abrió en tu computadora. "
                    "Comprueba que aparezcan los productos. "
                    "Después regresa a Streamlit."
                )

    except Exception as e:

        st.error(f"Error al abrir Amazon: {e}")


# ==========================================
# 7. EXTRAER PRODUCTOS
# ==========================================

if st.button("🔍 Extraer productos"):

    driver = st.session_state.driver

    if driver is None:

        st.warning(
            "Primero debes hacer clic en Abrir Amazon."
        )

    else:

        try:

            with st.spinner(
                "Esperando los resultados de Amazon..."
            ):

                try:

                    WebDriverWait(
                        driver, 20
                    ).until(

                        EC.presence_of_element_located(
                            (
                                By.CSS_SELECTOR,
                                '[data-component-type="s-search-result"]'
                            )
                        )
                    )

                except TimeoutException:

                    st.warning(
                        "No aparecieron productos "
                        "durante el tiempo de espera."
                    )

                html = driver.page_source

                titulo_pagina = driver.title
                url_actual = driver.current_url

            # Diagnóstico
            with st.expander(
                "🔧 Diagnóstico de extracción"
            ):

                st.write(
                    "Título de la página:",
                    titulo_pagina
                )

                st.write(
                    "URL actual:",
                    url_actual
                )

            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            resultados = soup.select(
                '[data-component-type="s-search-result"]'
            )

            # Detectar posibles verificaciones
            texto_pagina = soup.get_text(
                " ",
                strip=True
            ).lower()

            indicadores_bloqueo = [
                "enter the characters you see below",
                "robot check",
                "introduce los caracteres",
                "ingresa los caracteres",
                "automated access"
            ]

            if any(
                indicador in texto_pagina
                for indicador in indicadores_bloqueo
            ):

                st.error(
                    "Amazon parece estar mostrando "
                    "una página de verificación o "
                    "restricción de acceso automatizado."
                )

            st.write(
                f"🔎 Resultados HTML detectados: "
                f"{len(resultados)}"
            )

            productos = []

            # ==================================
            # 8. OBTENER DATOS DE CADA PRODUCTO
            # ==================================

            for item in resultados:

                titulo = item.select_one(
                    "h2 span"
                )

                precio = item.select_one(
                    ".a-price .a-offscreen"
                )

                enlace = item.select_one(
                    "h2 a[href]"
                )

                if titulo is None:
                    continue

                nombre_producto = titulo.get_text(
                    strip=True
                )

                precio_texto = (
                    precio.get_text(strip=True)
                    if precio
                    else "No disponible"
                )

                precio_numero = convertir_precio(
                    precio_texto
                )

                enlace_producto = (
                    urljoin(
                        "https://www.amazon.com.mx",
                        enlace.get("href")
                    )
                    if enlace
                    else ""
                )

                producto = {
                    "Producto": nombre_producto,
                    "Precio": precio_texto,
                    "Precio (MXN)": precio_numero,
                    "Enlace": enlace_producto
                }

                productos.append(producto)

            # ==================================
            # 9. GUARDAR RESULTADOS
            # ==================================

            if productos:

                df = pd.DataFrame(productos)

                st.session_state.productos = df

                st.success(
                    f"Se encontraron "
                    f"{len(df)} productos."
                )

            else:

                st.session_state.productos = None

                st.warning(
                    "No se encontraron productos. "
                    "Puede deberse a restricciones "
                    "de Amazon, cambios en el HTML "
                    "o resultados que no cargaron."
                )

        except WebDriverException as e:

            st.error(
                "El navegador no pudo completar "
                f"la extracción: {e}"
            )

        except Exception as e:

            st.error(
                f"Error durante la extracción: {e}"
            )


# ==========================================
# 10. MOSTRAR PRODUCTOS EN UNA TABLA
# ==========================================

if st.session_state.productos is not None:

    df = st.session_state.productos.copy()

    st.divider()

    st.subheader("📊 Productos encontrados")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.write(
        f"Total de productos: {len(df)}"
    )


    # ======================================
    # 11. FILTRAR PRODUCTOS POR PRECIO
    # ======================================

    st.divider()

    st.subheader("💰 Filtrar productos por precio")

    st.write(
        "Selecciona el precio mínimo y máximo "
        "de los productos que deseas visualizar."
    )

    precios_validos = df[
        "Precio (MXN)"
    ].dropna()

    if not precios_validos.empty:

        precio_maximo = float(
            precios_validos.max()
        )

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
                "El precio mínimo no puede "
                "ser mayor que el máximo."
            )

        else:

            # Aplicar filtros
            df_filtrado = df[
                (df["Precio (MXN)"] >= minimo)
                &
                (df["Precio (MXN)"] <= maximo)
            ].copy()

            # Ordenar los productos
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

            # ==================================
            # 12. MOSTRAR RESULTADOS FILTRADOS
            # ==================================

            st.divider()

            st.subheader("🛒 Resultados filtrados")

            st.write(
                f"Productos dentro del rango: "
                f"{len(df_filtrado)}"
            )

            if not df_filtrado.empty:

                st.dataframe(
                    df_filtrado,
                    use_container_width=True,
                    hide_index=True
                )

                # Resumen de precios
                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    st.metric(
                        "Productos",
                        len(df_filtrado)
                    )

                with col_b:
                    st.metric(
                        "Precio más bajo",
                        f"${df_filtrado['Precio (MXN)'].min():,.2f}"
                    )

                with col_c:
                    st.metric(
                        "Precio promedio",
                        f"${df_filtrado['Precio (MXN)'].mean():,.2f}"
                    )

                # ==================================
                # 13. DESCARGAR RESULTADOS
                # ==================================

                csv = df_filtrado.to_csv(
                    index=False
                ).encode("utf-8-sig")

                st.download_button(
                    label="📥 Descargar CSV filtrado",
                    data=csv,
                    file_name="productos_amazon_filtrados.csv",
                    mime="text/csv"
                )

            else:

                st.warning(
                    "No hay productos dentro "
                    "del rango seleccionado."
                )

        sin_precio = df[
            "Precio (MXN)"
        ].isna().sum()

        if sin_precio > 0:

            st.caption(
                f"{sin_precio} productos no tienen "
                "un precio válido y no se incluyen "
                "en el filtro."
            )

    else:

        st.warning(
            "Los productos extraídos no tienen "
            "precios válidos para filtrar."
        )

    # ======================================
    # 14. DESCARGAR TODOS LOS PRODUCTOS
    # ======================================

    st.divider()

    st.subheader("📁 Descargar todos los productos")

    csv_completo = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="📥 Descargar CSV completo",
        data=csv_completo,
        file_name="productos_amazon.csv",
        mime="text/csv"
    )


# ==========================================
# 15. INFORMACIÓN DEL PROYECTO
# ==========================================

st.divider()

st.caption(
    "Proyecto de Web Scraping desarrollado "
    "con Python, Streamlit, Selenium, "
    "BeautifulSoup y Pandas."
)
