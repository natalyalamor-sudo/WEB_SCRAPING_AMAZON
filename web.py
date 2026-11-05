        columns=["ASIN", "Producto", "Precio", "Calificación", "Enlace"],
    )


if "driver" not in st.session_state:
    st.session_state.driver = None
if "productos" not in st.session_state:
    st.session_state.productos = None

url = st.text_input(
    "Enlace de búsqueda:",
    "https://www.amazon.com.mx/s?k=lego+snoopy",
)

col1, col2, col3 = st.columns(3)

with col1:
    abrir = st.button(" Abrir Amazon", use_container_width=True)
with col2:
    extraer = st.button("Extraer productos", use_container_width=True)
with col3:
    cerrar = st.button(" Cerrar navegador", use_container_width=True)

if abrir:
    if not url.startswith(("https://www.amazon.com.mx/", "https://amazon.com.mx/")):
        st.error("Utiliza un enlace de Amazon México que empiece por https://www.amazon.com.mx/")
    else:
        if st.session_state.driver is not None:
            try:
                st.session_state.driver.quit()
            except Exception:
                pass
            st.session_state.driver = None
        st.session_state.productos = None

        navegador = None
        try:
            navegador = crear_navegador()
            navegador.get(url)
            st.session_state.driver = navegador
            st.success("Página abierta correctamente en el navegador de Selenium.")
            if ES_NUBE:
                st.info(
                    "En Streamlit Cloud, Chrome funciona sin ventana visible. "
                    "Si Amazon muestra un CAPTCHA, no podrás resolverlo aquí manualmente."
                )
            else:
                st.info(
                    "Si aparece un CAPTCHA, resuélvelo en la ventana de Chrome "
                    "y después presiona 'Extraer productos'."
                )
        except Exception as e:
            if navegador is not None:
                try:
                    navegador.quit()
                except Exception:
                    pass
            st.session_state.driver = None
            st.error(f"No se pudo abrir Chrome: {e}")

if extraer:
    navegador = st.session_state.driver
    if navegador is None:
        st.warning("Primero haz clic en 'Abrir Amazon'.")
    else:
        try:
            WebDriverWait(navegador, 15).until(
                lambda d: d.find_elements(
                    "css selector", '[data-component-type="s-search-result"]'
                )
                or "captcha" in d.current_url.lower()
                or "robot check" in d.title.lower()
            )
        except TimeoutException:
            pass

        try:
            html = navegador.page_source
            soup = BeautifulSoup(html, "html.parser")
            titulo_pagina = soup.title.get_text(" ", strip=True).lower() if soup.title else ""
            if (
                "captcha" in navegador.current_url.lower()
                or "robot check" in titulo_pagina
                or soup.select_one('form[action*="validateCaptcha"]')
            ):
                st.error(
                    "Amazon está mostrando un CAPTCHA. "
                    "En tu Mac puedes resolverlo en Chrome y volver a intentar; "
                    "en Streamlit Cloud no hay navegador visible."
                )
            else:
                datos = extraer_productos(html, navegador.current_url)
                if datos.empty:
                    st.warning(
                        "No se encontraron productos. Amazon puede haber bloqueado "
                        "la carga o cambiado la estructura de la página."
                    )
                else:
                    st.session_state.productos = datos
                    st.success(f"Se extrajeron {len(datos)} productos.")
        except WebDriverException as e:
            st.error(f"No se pudo leer la página: {e}")

if cerrar:
    if st.session_state.driver is not None:
        try:
            st.session_state.driver.quit()
        except Exception:
            pass
        st.session_state.driver = None
    st.info("Navegador cerrado.")

if st.session_state.productos is not None and not st.session_state.productos.empty:
    df = st.session_state.productos
    st.subheader("📊 Productos encontrados")
    st.dataframe(df, use_container_width=True, hide_index=True)

    archivo = BytesIO()
    with pd.ExcelWriter(archivo, engine="openpyxl") as escritor:
        df.to_excel(escritor, sheet_name="Productos Amazon", index=False)

    st.download_button(
        " Descargar Excel",
        data=archivo.getvalue(),
        file_name="productos_amazon.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


