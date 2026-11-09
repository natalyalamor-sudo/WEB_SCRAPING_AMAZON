# WEB_SCRAPING_AMAZON
Este proyecto consiste en el desarrollo de una aplicación web utilizando Python y Streamlit, cuyo objetivo es buscar, extraer, organizar y analizar información de productos disponibles en Amazon México.

La aplicación permite consultar productos y obtener información relevante, como nombres, precios, calificaciones, imágenes y enlaces, facilitando la comparación de productos y el análisis de precios.

El proyecto fue desarrollado con fines académicos para aplicar conocimientos de programación, extracción de datos y análisis de información.

Objetivos

- Desarrollar una aplicación web interactiva utilizando Python y Streamlit.
- Extraer información de productos disponibles en Amazon México.
- Organizar los datos mediante la librería Pandas.
- Facilitar la comparación de precios y características de los productos.
- Exportar los resultados a Excel para su posterior análisis.

Tecnologías utilizadas

 Tecnología | Función |

 Python | Lenguaje principal de programación. |
 Streamlit | Desarrollo de la interfaz web interactiva. |
 Selenium | Automatización del navegador para acceder a las páginas web. |
 BeautifulSoup | Extracción de información del contenido HTML. |
 Pandas | Organización y análisis de los datos obtenidos. |
 OpenPyXL | Exportación de información a Excel. |
 GitHub | Almacenamiento del código y control de versiones. |

 Funcionamiento de la aplicación

El funcionamiento de la aplicación consiste en los siguientes pasos:

1. El usuario introduce un enlace de búsqueda de Amazon México.
2. Selenium abre la página web mediante Google Chrome.
3. BeautifulSoup analiza el contenido HTML de la página.
4. Se extraen datos como nombre, precio, imagen y enlace de los productos.
5. La información obtenida se organiza mediante Pandas.
6. Los resultados se presentan en una tabla interactiva utilizando Streamlit.
7. El usuario puede descargar los resultados en formato Excel.

Instalación

Para ejecutar el proyecto de manera local, es necesario tener instalado Python y Google Chrome.

### 1. Clonar el repositorio

```bash
git clone https://github.com/USUARIO/REPOSITORIO.git
```

Reemplazar `USUARIO` y `REPOSITORIO` con los datos correspondientes.

### 2. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá en el navegador.

## Limitaciones

Amazon cuenta con mecanismos de seguridad que pueden restringir las solicitudes automatizadas, como los CAPTCHA.

En algunos casos, será necesario resolver manualmente estas verificaciones para continuar con la extracción de información.

Además, el funcionamiento de Selenium puede variar dependiendo del entorno de ejecución, las configuraciones del navegador y la disponibilidad de los elementos HTML.

Por esta razón, el funcionamiento local de la aplicación puede presentar diferencias respecto a su ejecución en Streamlit Cloud.

## Posibles mejoras

- Optimizar la extracción de información de los productos.
- Incorporar filtros por precio y categoría.
- Implementar herramientas para comparar productos.
- Agregar gráficas para visualizar las diferencias de precios.
- Mejorar la compatibilidad con diferentes entornos de ejecución.
- Ampliar las funciones de exportación y análisis de datos.

## Conclusión

El desarrollo de esta aplicación permite comprender el funcionamiento de las herramientas de extracción, procesamiento y visualización de datos mediante Python.

La integración de Selenium, BeautifulSoup, Pandas y Streamlit facilita la creación de una aplicación interactiva para consultar y organizar información de productos de Amazon México.

Este proyecto representa una aplicación práctica de conocimientos de programación, automatización web y análisis de datos, con posibilidades de mejora para futuros proyectos académicos.

## Autor

Nataly Alexandra Alatorre Moreno

Proyecto académico de programación en Python y análisis de datos.
