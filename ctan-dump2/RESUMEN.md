# Segunda ronda: horarios reales

## Qué líneas paran en cada una de nuestras paradas


  --- Telegrafía Sin Hilos (casa) (parada 7) ---
  404   /Consorcios/2/lineasPorParadas/7
      (ninguna)

  --- Campus-C. Educación (parada 79) ---
  404   /Consorcios/2/lineasPorParadas/79
      (ninguna)

  --- Campus-Ciencias (parada 81) ---
  404   /Consorcios/2/lineasPorParadas/81
      (ninguna)

  --- Escuela Ingeniería (parada 262) ---
  404   /Consorcios/2/lineasPorParadas/262
      (ninguna)

  --- Escuela Ingeniería (Interior) (parada 264) ---
  404   /Consorcios/2/lineasPorParadas/264
      (ninguna)

  En total 0 líneas distintas tocan alguna parada nuestra.

## Líneas que conectan casa con el campus

  Ninguna directa. Habrá que mirar transbordos.

## Horarios entre núcleos (Cádiz <-> Campus Universitario)


  --- Cádiz -> Campus ---
  ok    /Consorcios/2/horarios_origen_destino?origen=1&destino=41&lang=ES  -> Consorcios_2_horarios_origen_destino_origen_1_destino_41_lang_ES.json
      columnas: ['Lineas  ', 'Pz. España', 'Plaza de Sevilla-Estación de Cádiz', 'Pz.Asdrúbal-S.Sever.', 'Avda. Las Cortes', 'Hospital-Segunda Ag.', 'Telegrafía-Estadio', 'F. Ciencias Empresariales', 'Avda. de Huelva', 'C. Educación/Facultad Ciencias', 'Escuela Ingeniería', 'Frecuencia', 'Observaciones']
      84 filas de horario
        {'idlinea': '9', 'codigo': 'M-031', 'horas': ['06:00', '06:02', '--', '--', '--', '06:13', '--', '--', '06:26', '--'], 'dias': 'L-V', 'observaciones': '', 'demandahoras': '9,40647_1'}
        {'idlinea': '6', 'codigo': 'M-030', 'horas': ['06:20', '06:22', '06:26', '--', '06:30', '06:33', '--', '--', '06:47', '--'], 'dias': 'L-V', 'observaciones': 'SERVICIO ADAPTADO A PMR', 'demandahoras': '6,32575_1'}
        {'idlinea': '6', 'codigo': 'M-030', 'horas': ['06:40', '06:42', '06:46', '--', '06:50', '06:53', '--', '--', '07:07', '--'], 'dias': 'L-V', 'observaciones': 'SERVICIO ADAPTADO A PMR', 'demandahoras': '6,32576_1'}
        {'idlinea': '6', 'codigo': 'M-030', 'horas': ['07:00', '07:02', '07:06', '--', '07:10', '07:13', '--', '--', '07:27', '--'], 'dias': 'S-D-F', 'observaciones': 'SERVICIO ADAPTADO A PMR', 'demandahoras': '6,40762_5;40778_4'}

  --- Campus -> Cádiz ---
  ok    /Consorcios/2/horarios_origen_destino?origen=41&destino=1&lang=ES  -> Consorcios_2_horarios_origen_destino_origen_41_destino_1_lang_ES.json
      columnas: ['Lineas  ', 'Escuela Ingeniería', 'C. Educación/Facultad Ciencias', 'Telegrafía-Estadio', 'Hospital-Segunda Ag.', 'Avda. de Huelva', 'Pz.Asdrúbal-S.Sever.', 'F. Ciencias Empresariales', 'Avda. Las Cortes', 'Plaza de Sevilla-Estación de Cádiz', 'Pz. España', 'Frecuencia', 'Observaciones']
      86 filas de horario
        {'idlinea': '9', 'codigo': 'M-031', 'horas': ['--', '06:33', '06:48', '06:50', '--', '06:52', '--', '--', '06:55', '06:56'], 'dias': 'L-V', 'observaciones': 'SERVICIO ADAPTADO A PMR', 'demandahoras': '9,40655_1'}
        {'idlinea': '9', 'codigo': 'M-031', 'horas': ['--', '06:53', '07:08', '07:10', '--', '07:12', '--', '--', '07:15', '07:16'], 'dias': 'L-V', 'observaciones': '', 'demandahoras': '9,40656_1'}
        {'idlinea': '239', 'codigo': 'M-036', 'horas': ['--', '07:20', '--', '--', '--', '--', '--', '07:35', '07:41', '07:42'], 'dias': 'L-V', 'observaciones': '', 'demandahoras': '239,34846_1'}
        {'idlinea': '6', 'codigo': 'M-030', 'horas': ['--', '07:25', '07:42', '07:45', '--', '07:48', '--', '--', '07:53', '07:55'], 'dias': 'L-V', 'observaciones': 'SERVICIO ADAPTADO A PMR', 'demandahoras': '6,32606_1'}

  --- Cádiz -> Puerto Real ---
  ok    /Consorcios/2/horarios_origen_destino?origen=1&destino=6&lang=ES  -> Consorcios_2_horarios_origen_destino_origen_1_destino_6_lang_ES.json
      columnas: ['Lineas  ', 'Pz. España', 'Plaza de Sevilla-Estación de Cádiz', 'Pz.Asdrúbal-S.Sever.', 'Avda. Las Cortes', 'Hospital-Segunda Ag.', 'Telegrafía-Estadio', 'F. Ciencias Empresariales', 'Avda. de Huelva', '512 Viviendas', 'Cartabón/Huerta Pley', 'Casines/Ciudad Jardín', 'Estación FC', 'Las Aletas', 'Frecuencia', 'Observaciones']
      110 filas de horario
        {'idlinea': '214', 'codigo': 'MD', 'horas': ['--', '05:40', '--', '--', '--', '--', '--', '--', '--', '--', '--', '06:01', '--'], 'dias': 'L-V', 'observaciones': 'Tren media distancia que continúa a Sevilla', 'demandahoras': '214,39879_1'}
        {'idlinea': '9', 'codigo': 'M-031', 'horas': ['06:00', '06:02', '--', '--', '--', '06:13', '--', '--', '06:31', '06:34', '--', '--', '--'], 'dias': 'L-V', 'observaciones': '', 'demandahoras': '9,40647_1'}
        {'idlinea': '158', 'codigo': 'C-1', 'horas': ['--', '06:15', '06:17', '--', '06:19', '06:21', '--', '--', '--', '--', '--', '06:42', '06:45'], 'dias': 'L-V', 'observaciones': '', 'demandahoras': '158,38979_1'}
        {'idlinea': '6', 'codigo': 'M-030', 'horas': ['06:20', '06:22', '06:26', '--', '06:30', '06:33', '--', '--', '06:55', '06:58', '07:00', '--', '--'], 'dias': 'L-V', 'observaciones': 'SERVICIO ADAPTADO A PMR', 'demandahoras': '6,32575_1'}

  --- Puerto Real -> Cádiz ---
  ok    /Consorcios/2/horarios_origen_destino?origen=6&destino=1&lang=ES  -> Consorcios_2_horarios_origen_destino_origen_6_destino_1_lang_ES.json
      columnas: ['Lineas  ', 'Casines/Ciudad Jardín', 'Cartabón/Huerta Pley', '512 Viviendas', 'Las Aletas', 'Estación FC', 'Telegrafía-Estadio', 'Hospital-Segunda Ag.', 'Avda. de Huelva', 'Pz.Asdrúbal-S.Sever.', 'F. Ciencias Empresariales', 'Avda. Las Cortes', 'Plaza de Sevilla-Estación de Cádiz', 'Pz. España', 'Frecuencia', 'Observaciones']
      112 filas de horario
        {'idlinea': '9', 'codigo': 'M-031', 'horas': ['--', '06:20', '06:27', '--', '--', '06:48', '06:50', '--', '06:52', '--', '--', '06:55', '06:56'], 'dias': 'L-V', 'observaciones': 'SERVICIO ADAPTADO A PMR', 'demandahoras': '9,40655_1'}
        {'idlinea': '158', 'codigo': 'C-1', 'horas': ['--', '--', '--', '06:35', '06:38', '07:00', '07:02', '--', '07:04', '--', '--', '07:07', '--'], 'dias': 'L-V', 'observaciones': '', 'demandahoras': '158,39006_1'}
        {'idlinea': '9', 'codigo': 'M-031', 'horas': ['--', '06:40', '06:47', '--', '--', '07:08', '07:10', '--', '07:12', '--', '--', '07:15', '07:16'], 'dias': 'L-V', 'observaciones': '', 'demandahoras': '9,40656_1'}
        {'idlinea': '11', 'codigo': 'M-033', 'horas': ['06:50', '06:56', '07:02', '--', '--', '07:23', '07:25', '--', '07:27', '--', '--', '07:30', '07:31'], 'dias': 'L-V', 'observaciones': '', 'demandahoras': '11,40722_1'}

## Paradas y bloques de 0 líneas


## Horarios de línea (lo que de verdad necesitamos)

  Se piden sin filtros (devuelve todos los planificadores y frecuencias)
  y luego con dos fechas, para ver si el horario cambia en verano.

