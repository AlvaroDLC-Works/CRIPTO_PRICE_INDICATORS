# Proximas mejoras que falta pulir

- Agregar combinaciones de senales entre indicadores y reglas de entrada/salida.
- Separar el menu y el dashboard de estado en funciones reutilizables.
- Agregar filtros por rango a la herramienta de limpieza: dia, semana o anio.
- Registrar en un log `.txt` cada archivo eliminado por la herramienta de limpieza, incluyendo fecha y hora.
- crear diseño UIx con ventanas para el uso del script
- Agregar hora local para el nombre de archivos csv

# ------ Resuelto -------
- agrega archivo estado acrual al dashoard infirmativo del menu principal tambien

- al crear sistema de señales permite agregar mas de un indicador para que al final el archivo de salida sea una combinacion de los senales seleccionados csv file con una columna por resultado de indicador

- agrega opcion a eliminar sistemas de señales

- agregar opcion atras en menu sistema de señales disponibles 

- mueve el menu principa abajo y el dashboard informativo arriba

- cambiar 2) Editar configuracion (config/.env) por 2) Configurar Descarga (config/.env)

- cambiar 2) Editar configuracion (config/.env) en orden de menu por 1) Descargar datos (fetch_crypto_data) 
    El menu debe quedar en el siguiente orden:
    1) Configurar Descarga (config/.env)
    2) Descargar Datos (fetch_crypto_data)
    3) Analisis de Datos (analysis_data)
    4) Herramientas
    5) Salir

- Acortar nombre de los archivos CSV en un "unique ID con referencia a fecha de descarga" en todos los archivos de la carpeta data/
    - Genera un log file txt con el nombre acortado codido del archivo
    - Al lado una descripcion del archivo y la informacion del dashboard al momento de la descarga


- create *.bat version of CriptoPriceStart.ps1 in order to start script in command line and doble clic on explorer

- mueve los menus abajo y el dashboard informativo arriba en todos los menus y sub menus

- No veo el parametro SINCE en el menu: 
 === Editar configuracion config\.env ===
verifica el proceso para obtener este menu:
Lee archivo .env para determinar cantidad y nombre de parametros, en base a esa lista crea archivo json a ser usado en codigo para generar el menu y poder editar todos los parametros que se deseen.

- crear menu graficos en el menu principal debajo de 3) Analisis de Datos. como 4) Graficos y recocorrer el resto de opciones para abajo
Menu Graficos
1) ver en pantalla: (por velas tipo trading view) 
2) exportar grafico en pdf :(como un screenshot del primero en pdf hazlo en horizontal) 
3) exportar grafico en cad/dxf:
    a) para cada columna de datos usar un layer diferente 
    b) usa el eje x para representar tiempo y el y con el valor resultante en la columna evaluada.
    c) da la opcion de elegir si van unidos por una polilinea o si son solo puntos
    d) en el caso de polilineas pon el punto con el simbolo punto
    e) en el caso de solo punto usa el simbolo de X 
    No es necesario representar las velas en el grafico cad/dxf solo puntos y polilineas que sean unidos a travez del eje x

# ----- Pendientes -------

- agregar opcion de bajar solo uno o miltiles indicadores sin los datos base



