# Reconocimiento de api.ctan.es

Base: https://api.ctan.es

## Documentación de la API

  ok    /doc/api_data.json  (lista de 60) -> ctan-dump\doc_api_data_json.json
  ok    /doc/api_project.json  (dict con claves ['name', 'version', 'description', 'title', 'url', 'sampleUrl']) -> ctan-dump\doc_api_project_json.json
  ok    /doc/  (29,287 bytes, html) -> ctan-dump\doc.html
  ok    /doc/index.html  (29,287 bytes, html) -> ctan-dump\doc_index_html.html

  La documentación describe 60 endpoints:
    GET    /Consorcios/:idConsorcio/abreviaturas   Abreviaturas
    GET    /Consorcios/:idConsorcio/frecuencias   Frecuencias
    GET    /Consorcios/:idConsorcio/att_usuario   Obtiene atencion al usuario
    GET    /Consorcios/:idConsorcio/configuracion   Configuracion de la App
    GET    /Consorcios/:idConsorcio/consorcios   Lista de Consorcios
    GET    /Consorcios/consorcios   Consorcios por defecto
    GET    /Consorcios/:idConsorcio/consorcio   Datos del Consorcio
    GET    /Consorcios/:idConsorcio/corredores/:idCorredor/bloques   Bloques de paso
    GET    /Consorcios/:idConsorcio/corredores/:idCorredor   Obtiene corredor
    GET    /Consorcios/:idConsorcio/corredores/   Listado
    GET    /Consorcios/:idConsorcio/horarios_lineas   Horario de una línea
    GET    /Consorcios/:idConsorcio/horarios_origen_destino   Horarios de las líneas entre un núcleo de origen y un núcleo de destino determinado
    GET    /Consorcios/:idConsorcio/horarios_corredor   Horarios de las líneas de un corredor
    GET    /Consorcios/:idConsorcio/idiomas   Idiomas del Consorcio
    GET    /Consorcios/:idConsorcio/:idLinea   Datos de una línea
    GET    /Consorcios/:idConsorcio/lineas/:codigo   Datos de una línea, por su código
    GET    /Consorcios/:idConsorcio/infoLineas/:idLineas   Datos de varias líneas, dados por su identificador
    GET    /Consorcios/:idConsorcio/corredores/:idLinea/bloques   Bloques de paso
    GET    /Consorcios/:idConsorcio/lineas   Lineas del consorcio
    GET    /Consorcios/:idConsorcio/modostransporte/:idModo/lineas   Listado de líneas por modo de transporte
    GET    /Consorcios/:idConsorcio/municipios/:idMunicipio/nucleos/:idnucleo/lineas   Listado de líneas por municipios y núcleo
    GET    /Consorcios/:idConsorcio/nucleos/:idNucleo/lineas   Listado de lineas por nucleo
    GET    /Consorcios/:idConsorcio/lineas/:idLinea/paradas   Paradas de una línea
    GET    /Consorcios/:idConsorcio/lugares_interes/:idLugar   Datos del lugar de interés
    GET    /Consorcios/:idConsorcio/lugares_interes/:idLugar   Lista de lugares de interes de un tipo y de un municipio
    GET    /Consorcios/:idConsorcio/lugares_interes   Listado de lugares de interés del Consorcio
    GET    /Consorcios/:idConsorcio/municipios/:idMunicipio/lugares_interes   Lista de lugares de interés de un municipio y un tipo
    GET    /Consorcios/:idConsorcio/tipos_lugares_interes/:idCat   Datos del tipo de lugar de interés
    GET    /Consorcios/:idConsorcio/tipos_lugares_interes/   Tipos de lugares de interés
    GET    /Consorcios/:idConsorcio/modostransporte   Modos de transporte
    GET    /Consorcios/:idConsorcio/modostransporte/:id   Modo Modos de transporte con identificador
    GET    /Consorcios/:idConsorcio/municipios/:id   Datos de un municipio
    GET    /Consorcios/:idConsorcio/municipios/   Lista de municipios
    GET    /Consorcios/:idConsorcio/categorias_noticias   Categorías de las noticias
    GET    /Consorcios/:idConsorcio/noticias/:idNoticia   Detalles de una noticia
    GET    /Consorcios/:idConsorcio/categorias_noticias/:idCategoria/noticias   Noticias filtradas por parámetros
    GET    /Consorcios/:idConsorcio/lineas/:idLinea/noticias   Noticias de una linea
    GET    /Consorcios/:idConsorcio/noticias   Lista de noticias
    GET    /Consorcios/:idConsorcio/infoLineasNoticias/:idLineas   Lista de noticias dados los identificadores de varias líneas
    GET    /Consorcios/:idConsorcio/nucleos/:idNucleo   Datos de un nucleo
    GET    /Consorcios/:idConsorcio/nucleos   Lista de nucleos
    GET    /Consorcios/:idConsorcio/municipios/:idMunicipio/nucleos   Lista de nucleos de un municipio
    GET    /Consorcios/:idConsorcio/infoParadas/:idParadas   Información de paradas
    GET    /Consorcios/:idConsorcio/lineasPorParadas/:idParadas   Lista de líneas que pasan por paradas
    GET    /Consorcios/:idConsorcio/paradas/:idParada   Datos de una parada
    GET    /Consorcios/:idConsorcio/paradas/   Lista de paradas del Consorcio
    GET    /Consorcios/:idConsorcio/municipios/:idMunicipio/nucleos/:idnucleo/paradas   Listado de paradas por municipios y núcleo
    GET    /Consorcios/:idConsorcio/nucleos/:idNucleo/paradas   Listado de paradas por nucleo
    GET    /Consorcios/:idConsorcio/zonas/idZona/paradas   Paradas por zona
    GET    /Consorcios/:idConsorcio/paradas/:idParada/servicios   Servicios que pasan por un parada
    GET    /Consorcios/:idConsorcio/politica_privacidad   Politica Privacidad
    GET    /Consorcios/:idConsorcio/puntos_venta   Datos de un punto de venta
    GET    /Consorcios/:idConsorcio/puntos_venta   Lista de puntos de venta del Consorcio
    GET    /Consorcios/:idConsorcio/puntos_venta   Lista de puntos de venta por municipio,nucleo y tipo
    GET    /Consorcios/:idConsorcio/puntos_venta   Tipos de puntos de venta
    GET    /Consorcios/:idConsorcio/saltos   Saltos entre zonas
    GET    /Consorcios/:idConsorcio/calculo_saltos/   Saltos entre núcleos
    GET    /Consorcios/:idConsorcio/tarifas_interurbanas   Tarifas Interurbanas
    GET    /Consorcios/:idConsorcio/tarifas_urbanas   Tarifas Urbanas
    GET    /Consorcios/:idConsorcio/zonas   Zonas

## Consorcios

  404   /v1/Consorcios

  No he sabido deducir el id. Pruebo con 2, que suele ser Bahía de Cádiz.

  Consorcio elegido: 2

## Recursos del consorcio

  404   /v1/Consorcios/2
  ok    /v1/Consorcios/2/municipios  (dict con 'municipios' de 15) -> ctan-dump\v1_Consorcios_2_municipios.json
  ok    /v1/Consorcios/2/nucleos  (dict con 'nucleos' de 44) -> ctan-dump\v1_Consorcios_2_nucleos.json
  ok    /v1/Consorcios/2/zonas  (dict con 'zonas' de 22) -> ctan-dump\v1_Consorcios_2_zonas.json
  404   /v1/Consorcios/2/modos
  ok    /v1/Consorcios/2/operadores  (lista de 11) -> ctan-dump\v1_Consorcios_2_operadores.json
  ok    /v1/Consorcios/2/lineas  (dict con 'lineas' de 70) -> ctan-dump\v1_Consorcios_2_lineas.json
  ok    /v1/Consorcios/2/paradas  (dict con 'paradas' de 181) -> ctan-dump\v1_Consorcios_2_paradas.json
  ok    /v1/Consorcios/2/frecuencias  (dict con 'frecuencias' de 15) -> ctan-dump\v1_Consorcios_2_frecuencias.json
  ok    /v1/Consorcios/2/noticias  (dict con 'noticias' de 16) -> ctan-dump\v1_Consorcios_2_noticias.json
  404   /v1/Consorcios/2/tarifas

## Nuestras paradas

  4 coincidencias:

    {"idParada": "79", "idNucleo": "41", "idZona": "F", "nombre": "Campus-C. Educación", "latitud": "36.527558", "longitud": "-6.213559", "idMunicipio": "4", "municipio": "Puerto Real", "nucleo": "Campus Universitario"}
    {"idParada": "262", "idNucleo": "41", "idZona": "F", "nombre": "Escuela Ingeniería", "latitud": "36.53687476012414", "longitud": "-6.200977563858032", "idMunicipio": "4", "municipio": "Puerto Real", "nucleo": "Campus Universitario"}
    {"idParada": "264", "idNucleo": "41", "idZona": "F", "nombre": "Escuela Ingeniería (Interior)", "latitud": "36.536704179923404", "longitud": "-6.20187939574726", "idMunicipio": "4", "municipio": "Puerto Real", "nucleo": "Campus Universitario"}
    {"idParada": "7", "idNucleo": "1", "idZona": "A", "nombre": "Telegrafía Sin Hilos", "latitud": "36.500057150866574", "longitud": "-6.273421347141266", "idMunicipio": "1", "municipio": "Cádiz", "nucleo": "Cádiz"}

## Líneas que pasan por esas paradas

  ok    /v1/Consorcios/2/paradas/79  (dict con claves ['idParada', 'idNucleo', 'idMunicipio', 'idZona', 'nombre', 'latitud']) -> ctan-dump\v1_Consorcios_2_paradas_79.json
  ok    /v1/Consorcios/2/paradas/79/servicios  (dict con 'servicios' de 3) -> ctan-dump\v1_Consorcios_2_paradas_79_servicios.json
  ok    /v1/Consorcios/2/paradas/262  (dict con claves ['idParada', 'idNucleo', 'idMunicipio', 'idZona', 'nombre', 'latitud']) -> ctan-dump\v1_Consorcios_2_paradas_262.json
  ok    /v1/Consorcios/2/paradas/262/servicios  (dict con 'servicios' de 0) -> ctan-dump\v1_Consorcios_2_paradas_262_servicios.json
  ok    /v1/Consorcios/2/paradas/264  (dict con claves ['idParada', 'idNucleo', 'idMunicipio', 'idZona', 'nombre', 'latitud']) -> ctan-dump\v1_Consorcios_2_paradas_264.json
  ok    /v1/Consorcios/2/paradas/264/servicios  (dict con 'servicios' de 0) -> ctan-dump\v1_Consorcios_2_paradas_264_servicios.json
  ok    /v1/Consorcios/2/paradas/7  (dict con claves ['idParada', 'idNucleo', 'idMunicipio', 'idZona', 'nombre', 'latitud']) -> ctan-dump\v1_Consorcios_2_paradas_7.json
  ok    /v1/Consorcios/2/paradas/7/servicios  (dict con 'servicios' de 11) -> ctan-dump\v1_Consorcios_2_paradas_7_servicios.json

## Horarios (muestra)

  70 líneas en el consorcio. Bajo el detalle de las 6 primeras
  y de cualquiera cuyo nombre mencione Puerto Real o el campus.

  ok    /v1/Consorcios/2/lineas/15  (dict con 'polilinea' de 38) -> ctan-dump\v1_Consorcios_2_lineas_15.json
  ok    /v1/Consorcios/2/lineas/15/paradas  (dict con 'paradas' de 4) -> ctan-dump\v1_Consorcios_2_lineas_15_paradas.json
  404   /v1/Consorcios/2/lineas/15/horarios
  404   /v1/Consorcios/2/lineas/15/horarios_lineas
  404   /v1/Consorcios/2/lineas/15/itinerario
  ok    /v1/Consorcios/2/lineas/22  (dict con 'polilinea' de 41) -> ctan-dump\v1_Consorcios_2_lineas_22.json
  ok    /v1/Consorcios/2/lineas/22/paradas  (dict con 'paradas' de 4) -> ctan-dump\v1_Consorcios_2_lineas_22_paradas.json
  404   /v1/Consorcios/2/lineas/22/horarios
  404   /v1/Consorcios/2/lineas/22/horarios_lineas
  404   /v1/Consorcios/2/lineas/22/itinerario
  ok    /v1/Consorcios/2/lineas/158  (dict con 'polilinea' de 882) -> ctan-dump\v1_Consorcios_2_lineas_158.json
  ok    /v1/Consorcios/2/lineas/158/paradas  (dict con 'paradas' de 28) -> ctan-dump\v1_Consorcios_2_lineas_158_paradas.json
  404   /v1/Consorcios/2/lineas/158/horarios
  404   /v1/Consorcios/2/lineas/158/horarios_lineas
  404   /v1/Consorcios/2/lineas/158/itinerario
  ok    /v1/Consorcios/2/lineas/2  (dict con 'polilinea' de 363) -> ctan-dump\v1_Consorcios_2_lineas_2.json
  ok    /v1/Consorcios/2/lineas/2/paradas  (dict con 'paradas' de 32) -> ctan-dump\v1_Consorcios_2_lineas_2_paradas.json
  404   /v1/Consorcios/2/lineas/2/horarios
  404   /v1/Consorcios/2/lineas/2/horarios_lineas
  404   /v1/Consorcios/2/lineas/2/itinerario
  ok    /v1/Consorcios/2/lineas/3  (dict con 'polilinea' de 389) -> ctan-dump\v1_Consorcios_2_lineas_3.json
  ok    /v1/Consorcios/2/lineas/3/paradas  (dict con 'paradas' de 32) -> ctan-dump\v1_Consorcios_2_lineas_3_paradas.json
  404   /v1/Consorcios/2/lineas/3/horarios
  404   /v1/Consorcios/2/lineas/3/horarios_lineas
  404   /v1/Consorcios/2/lineas/3/itinerario
  ok    /v1/Consorcios/2/lineas/4  (dict con 'polilinea' de 506) -> ctan-dump\v1_Consorcios_2_lineas_4.json
  ok    /v1/Consorcios/2/lineas/4/paradas  (dict con 'paradas' de 21) -> ctan-dump\v1_Consorcios_2_lineas_4_paradas.json
  404   /v1/Consorcios/2/lineas/4/horarios
  404   /v1/Consorcios/2/lineas/4/horarios_lineas
  404   /v1/Consorcios/2/lineas/4/itinerario
  ok    /v1/Consorcios/2/lineas/5  (dict con 'polilinea' de 639) -> ctan-dump\v1_Consorcios_2_lineas_5.json
  ok    /v1/Consorcios/2/lineas/5/paradas  (dict con 'paradas' de 19) -> ctan-dump\v1_Consorcios_2_lineas_5_paradas.json
  404   /v1/Consorcios/2/lineas/5/horarios
  404   /v1/Consorcios/2/lineas/5/horarios_lineas
  404   /v1/Consorcios/2/lineas/5/itinerario
  ok    /v1/Consorcios/2/lineas/6  (dict con 'polilinea' de 840) -> ctan-dump\v1_Consorcios_2_lineas_6.json
  ok    /v1/Consorcios/2/lineas/6/paradas  (dict con 'paradas' de 35) -> ctan-dump\v1_Consorcios_2_lineas_6_paradas.json
  404   /v1/Consorcios/2/lineas/6/horarios
  404   /v1/Consorcios/2/lineas/6/horarios_lineas
  404   /v1/Consorcios/2/lineas/6/itinerario
  ok    /v1/Consorcios/2/lineas/9  (dict con 'polilinea' de 604) -> ctan-dump\v1_Consorcios_2_lineas_9.json
  ok    /v1/Consorcios/2/lineas/9/paradas  (dict con 'paradas' de 28) -> ctan-dump\v1_Consorcios_2_lineas_9_paradas.json
  404   /v1/Consorcios/2/lineas/9/horarios
  404   /v1/Consorcios/2/lineas/9/horarios_lineas
  404   /v1/Consorcios/2/lineas/9/itinerario
  ok    /v1/Consorcios/2/lineas/10  (dict con 'polilinea' de 582) -> ctan-dump\v1_Consorcios_2_lineas_10.json
  ok    /v1/Consorcios/2/lineas/10/paradas  (dict con 'paradas' de 22) -> ctan-dump\v1_Consorcios_2_lineas_10_paradas.json
  404   /v1/Consorcios/2/lineas/10/horarios
  404   /v1/Consorcios/2/lineas/10/horarios_lineas
  404   /v1/Consorcios/2/lineas/10/itinerario

