# Revisión de calidad — CNSF agrícola (emisión + siniestros, 2008-2024)

Barrido sistemático de los consolidados; generaliza el hallazgo Maíz dulce/Sinaloa/2015.
**Nada se ha modificado**: cada grupo lista su acción propuesta, a aprobar item por item.
Consolidados leídos de `/Users/lescobarfarfan/Documents/projects/Thesis_MScQF/climateCCR/data/hazard_mx/datos_CNSF/consolidados/agricola_y_animales`.

**Total hallazgos: 2133** · propuestas de corrección ÷1000 a nivel renglón: 113 (`renglones_correccion_propuesta.csv`)

| chequeo | severidad | n | acción propuesta |
|---|---|---|---|
| B1_superficie_mayor_al_estado | critica | 11 | corregir_o_excluir |
| B2_valor_implicito_bajo | critica | 21 | corregir_div1000 |
| A3_moneda_no_nacional | alta | 2 | separar_moneda |
| B2_valor_implicito_alto | alta | 225 | revisar |
| B2_valor_implicito_bajo | alta | 170 | revisar |
| B3_siniestrada_mayor_asegurada | alta | 110 | revisar |
| A1_variantes_categoricas | media | 72 | normalizar |
| A2_entidad_no_estatal | media | 2 | excluir_de_vistas_estatales |
| B2_valor_implicito_alto | media | 614 | revisar |
| B3_siniestrada_mayor_asegurada | media | 164 | revisar |
| B3b_siniestro_sin_emision | media | 196 | revisar |
| B4_pagado_mayor_suma | media | 109 | revisar |
| B5_salto_superficie_atipico | media | 433 | revisar |
| A4_valores_negativos | baja | 3 | revisar |
| A6_superficie_cero_con_suma | baja | 1 | revisar |

## A1_variantes_categoricas — 72 hallazgos

```
anio entidad cultivo  valor                                                                                                         detalle accion_propuesta
                          3 CICLO DE CULTIVO: {'No disponible': 119, 'No Disponible': 193, 'No disponible ': 20} colapsan a 'NO DISPONIBLE'       normalizar
                          3           MONEDA: {'No disponible': 104, 'No Disponible': 193, 'No disponible ': 35} colapsan a 'NO DISPONIBLE'       normalizar
                          2                         ENTIDAD: {'ESTADO DE MEXICO': 7, 'Estado de México': 279} colapsan a 'ESTADO DE MEXICO'       normalizar
                          2                                          ENTIDAD: {'MICHOACAN': 1090, 'Michoacán': 1774} colapsan a 'MICHOACAN'       normalizar
                          2                                                      ENTIDAD: {'México': 26, 'MEXICO': 141} colapsan a 'MEXICO'       normalizar
                          2                                                 ENTIDAD: {'JALISCO': 861, 'Jalisco': 2016} colapsan a 'JALISCO'       normalizar
                          2                                                  ENTIDAD: {'HIDALGO': 333, 'Hidalgo': 627} colapsan a 'HIDALGO'       normalizar
                          2                                                ENTIDAD: {'GUERRERO': 75, 'Guerrero': 122} colapsan a 'GUERRERO'       normalizar
                          2                                       ENTIDAD: {'GUANAJUATO': 1407, 'Guanajuato': 2879} colapsan a 'GUANAJUATO'       normalizar
                          2                                                  ENTIDAD: {'DURANGO': 146, 'Durango': 428} colapsan a 'DURANGO'       normalizar
                          2                                                  ENTIDAD: {'NAYARIT': 575, 'Nayarit': 916} colapsan a 'NAYARIT'       normalizar
                          2                         ENTIDAD: {'DISTRITO FEDERAL': 12, 'Distrito Federal': 60} colapsan a 'DISTRITO FEDERAL'       normalizar
                          2                                                     ENTIDAD: {'COLIMA': 159, 'Colima': 241} colapsan a 'COLIMA'       normalizar
                          2                                                ENTIDAD: {'COAHUILA': 87, 'Coahuila': 190} colapsan a 'COAHUILA'       normalizar
                          2                                            ENTIDAD: {'CHIHUAHUA': 384, 'Chihuahua': 845} colapsan a 'CHIHUAHUA'       normalizar
```
(+57 más en `hallazgos_agricola.csv`)

## A2_entidad_no_estatal — 2 hallazgos

```
anio entidad cultivo  valor                                                                                 detalle            accion_propuesta
                        252      252 renglones ENTIDAD∈['EN EL EXTRANJERO', 'Extranjero'], MONTO PAGADO=413,816,198 excluir_de_vistas_estatales
                        177 177 renglones ENTIDAD∈['EN EL EXTRANJERO', 'Extranjero'], SUMA ASEGURADA=10,211,524,769 excluir_de_vistas_estatales
```

## A3_moneda_no_nacional — 2 hallazgos

```
anio entidad cultivo  valor                                                                                                                                                                      detalle accion_propuesta
                       1265 1265 renglones MONEDA≠Nacional (['Extranjera', 'No Disponible', 'No disponible', 'No disponible ']); % de MONTO PAGADO por año, peores: {2009: 11.8, 2008: 11.3, 2024: 11.2}   separar_moneda
                       1136                                                     1136 renglones MONEDA≠Nacional (['Extranjera']); % de SUMA ASEGURADA por año, peores: {2008: 23.6, 2020: 9.1, 2021: 8.6}   separar_moneda
```

## A4_valores_negativos — 3 hallazgos

```
anio entidad cultivo  valor                                                                                                                                                                                                                                                                                                                                                 detalle accion_propuesta
                       3686 MONTO DEL SINIESTRO OCURRIDO: 3686 renglones, suma=-604,313,335 (años [np.int64(2008), np.int64(2009), np.int64(2010), np.int64(2011), np.int64(2012), np.int64(2013), np.int64(2014), np.int64(2015), np.int64(2016), np.int64(2017), np.int64(2018), np.int64(2019), np.int64(2020), np.int64(2021), np.int64(2022), np.int64(2023), np.int64(2024)])          revisar
                       1200                PRIMA EMITIDA: 1200 renglones, suma=-349,504,966 (años [np.int64(2008), np.int64(2009), np.int64(2010), np.int64(2011), np.int64(2012), np.int64(2013), np.int64(2014), np.int64(2015), np.int64(2016), np.int64(2017), np.int64(2018), np.int64(2019), np.int64(2020), np.int64(2021), np.int64(2022), np.int64(2023), np.int64(2024)])          revisar
                          4                                                                                                                                                                                                                                                         MONTO PAGADO: 4 renglones, suma=-36,825 (años [np.int64(2011), np.int64(2019), np.int64(2020)])          revisar
```

## A6_superficie_cero_con_suma — 1 hallazgos

```
anio entidad cultivo  valor                                                                                                                        detalle accion_propuesta
                          1 1 renglones agrícolas con superficie 0 y SUMA ASEGURADA>0 (pólizas no por-hectárea o superficie faltante); distorsionan MXN/ha          revisar
```

## B1_superficie_mayor_al_estado — 11 hallazgos

```
anio          entidad      cultivo    valor                                                        detalle   accion_propuesta
2010          CHIAPAS         MAIZ 49479253 SUPERFICIE SINIESTRADA=49,479,253 ha > territorio 7,361,736 ha corregir_o_excluir
2011          CHIAPAS         MAIZ 39640205 SUPERFICIE SINIESTRADA=39,640,205 ha > territorio 7,361,736 ha corregir_o_excluir
2015        MICHOACAN     AGUACATE 13881008   SUPERFICIE ASEGURADA=13,881,008 ha > territorio 5,830,145 ha corregir_o_excluir
2016        MICHOACAN     AGUACATE  9661230    SUPERFICIE ASEGURADA=9,661,230 ha > territorio 5,830,145 ha corregir_o_excluir
2015       GUANAJUATO    ESPARRAGO  9543600  SUPERFICIE SINIESTRADA=9,543,600 ha > territorio 3,033,977 ha corregir_o_excluir
2015          SINALOA   MAIZ DULCE  6104409    SUPERFICIE ASEGURADA=6,104,409 ha > territorio 5,681,563 ha corregir_o_excluir
2015       GUANAJUATO        TRIGO  5342032  SUPERFICIE SINIESTRADA=5,342,032 ha > territorio 3,033,977 ha corregir_o_excluir
2017 CIUDAD DE MEXICO OTRO CULTIVO  5148817      SUPERFICIE ASEGURADA=5,148,817 ha > territorio 147,706 ha corregir_o_excluir
2018 CIUDAD DE MEXICO OTRO CULTIVO  5144439      SUPERFICIE ASEGURADA=5,144,439 ha > territorio 147,706 ha corregir_o_excluir
2015       GUANAJUATO      CEBOLLA  4311963    SUPERFICIE ASEGURADA=4,311,963 ha > territorio 3,033,977 ha corregir_o_excluir
2015       GUANAJUATO    ESPARRAGO  3181400    SUPERFICIE ASEGURADA=3,181,400 ha > territorio 3,033,977 ha corregir_o_excluir
```

## B2_valor_implicito_alto — 839 hallazgos

```
anio         entidad        cultivo     valor                                                                                                 detalle accion_propuesta
2022         CHIAPAS          AGAVE 107259205    107,259,205 MXN/ha (sup 11 ha; suma 1,178,778,662): posible sub-reporte de superficie o suma inflada          revisar
2023         CHIAPAS          AGAVE  93376485     93,376,485 MXN/ha (sup 19 ha; suma 1,767,616,870): posible sub-reporte de superficie o suma inflada          revisar
2024         CHIAPAS          AGAVE  65982838     65,982,838 MXN/ha (sup 33 ha; suma 2,165,556,728): posible sub-reporte de superficie o suma inflada          revisar
2022         JALISCO       ARANDANO  42079681 42,079,681 MXN/ha (sup 1,093 ha; suma 46,004,453,037): posible sub-reporte de superficie o suma inflada          revisar
2024         JALISCO       ARANDANO  36914406   36,914,406 MXN/ha (sup 671 ha; suma 24,783,224,719): posible sub-reporte de superficie o suma inflada          revisar
2024         JALISCO         PEPINO  32259308       32,259,308 MXN/ha (sup 19 ha; suma 627,766,134): posible sub-reporte de superficie o suma inflada          revisar
2023         JALISCO       ARANDANO  26293736 26,293,736 MXN/ha (sup 1,328 ha; suma 34,908,352,283): posible sub-reporte de superficie o suma inflada          revisar
2024         JALISCO PIMIENTO MORON  23201308     23,201,308 MXN/ha (sup 44 ha; suma 1,029,210,034): posible sub-reporte de superficie o suma inflada          revisar
2023         CHIAPAS       ARANDANO  20235859       20,235,859 MXN/ha (sup 12 ha; suma 242,830,306): posible sub-reporte de superficie o suma inflada          revisar
2024      GUANAJUATO          CHILE  15981728       15,981,728 MXN/ha (sup 62 ha; suma 990,547,517): posible sub-reporte de superficie o suma inflada          revisar
2022 SAN LUIS POTOSI       ARANDANO  14025226       14,025,226 MXN/ha (sup 16 ha; suma 224,403,620): posible sub-reporte de superficie o suma inflada          revisar
2022         SINALOA       ARANDANO  13199651    13,199,651 MXN/ha (sup 110 ha; suma 1,457,637,435): posible sub-reporte de superficie o suma inflada          revisar
2024        COAHUILA         PEPINO  12529740       12,529,740 MXN/ha (sup 25 ha; suma 313,243,500): posible sub-reporte de superficie o suma inflada          revisar
2024          SONORA         TOMATE  12245880    12,245,880 MXN/ha (sup 428 ha; suma 5,240,869,080): posible sub-reporte de superficie o suma inflada          revisar
2013       QUERETARO         TOMATE  12000000       12,000,000 MXN/ha (sup 10 ha; suma 120,000,000): posible sub-reporte de superficie o suma inflada          revisar
```
(+824 más en `hallazgos_agricola.csv`)

## B2_valor_implicito_bajo — 191 hallazgos

```
anio         entidad  cultivo  valor                                                   detalle accion_propuesta
2012         JALISCO GARBANZO    993       993 MXN/ha (sup 671 ha); ÷1000 daría 993,331 MXN/ha          revisar
2010      TAMAULIPAS    SORGO    987   987 MXN/ha (sup 449,980 ha); ÷1000 daría 987,427 MXN/ha          revisar
2010 SAN LUIS POTOSI    SORGO    984    984 MXN/ha (sup 16,521 ha); ÷1000 daría 984,325 MXN/ha          revisar
2011          MEXICO   FRIJOL    983       983 MXN/ha (sup 808 ha); ÷1000 daría 982,649 MXN/ha          revisar
2010        TLAXCALA    TRIGO    982    982 MXN/ha (sup 27,366 ha); ÷1000 daría 982,126 MXN/ha          revisar
2012    QUINTANA ROO   FRIJOL    975     975 MXN/ha (sup 2,502 ha); ÷1000 daría 975,000 MXN/ha          revisar
2013       MICHOACAN  LENTEJA    975       975 MXN/ha (sup 550 ha); ÷1000 daría 975,000 MXN/ha          revisar
2012         DURANGO   CEBADA    975       975 MXN/ha (sup 503 ha); ÷1000 daría 975,000 MXN/ha          revisar
2008         NAYARIT    SORGO    973    973 MXN/ha (sup 37,581 ha); ÷1000 daría 972,633 MXN/ha          revisar
2010        VERACRUZ    SORGO    968    968 MXN/ha (sup 67,183 ha); ÷1000 daría 967,849 MXN/ha          revisar
2010         CHIAPAS     MAIZ    966 966 MXN/ha (sup 1,444,768 ha); ÷1000 daría 965,516 MXN/ha          revisar
2008         HIDALGO     MAIZ    963   963 MXN/ha (sup 239,877 ha); ÷1000 daría 963,199 MXN/ha          revisar
2008         SINALOA    SORGO    962    962 MXN/ha (sup 93,360 ha); ÷1000 daría 961,611 MXN/ha          revisar
2010       QUERETARO     MAIZ    957    957 MXN/ha (sup 60,304 ha); ÷1000 daría 956,756 MXN/ha          revisar
2009        VERACRUZ     MAIZ    957   957 MXN/ha (sup 786,703 ha); ÷1000 daría 957,303 MXN/ha          revisar
```
(+176 más en `hallazgos_agricola.csv`)

## B3_siniestrada_mayor_asegurada — 274 hallazgos

```
anio         entidad   cultivo    valor                                                         detalle accion_propuesta
2010         CHIAPAS      MAIZ 49479253 siniestrada 49,479,253 ha > asegurada 1,444,768 ha (ratio 34.2)          revisar
2011         CHIAPAS      MAIZ 39640205 siniestrada 39,640,205 ha > asegurada 1,555,053 ha (ratio 25.5)          revisar
2015      GUANAJUATO ESPARRAGO  9543600   siniestrada 9,543,600 ha > asegurada 3,181,400 ha (ratio 3.0)          revisar
2015      GUANAJUATO     TRIGO  5342032   siniestrada 5,342,032 ha > asegurada 2,428,457 ha (ratio 2.2)          revisar
2015 SAN LUIS POTOSI     CHILE  1394822     siniestrada 1,394,822 ha > asegurada 515,199 ha (ratio 2.7)          revisar
2015    QUINTANA ROO      CANA   507298        siniestrada 507,298 ha > asegurada 81,076 ha (ratio 6.3)          revisar
2016    QUINTANA ROO      CANA   360633       siniestrada 360,633 ha > asegurada 100,676 ha (ratio 3.6)          revisar
2020         JALISCO      MAIZ   306369        siniestrada 306,369 ha > asegurada 55,080 ha (ratio 5.6)          revisar
2010         YUCATAN      MAIZ   233961       siniestrada 233,961 ha > asegurada 225,257 ha (ratio 1.0)          revisar
2021         JALISCO      MAIZ   179948        siniestrada 179,948 ha > asegurada 57,509 ha (ratio 3.1)          revisar
2023         JALISCO      MAIZ   164073        siniestrada 164,073 ha > asegurada 54,331 ha (ratio 3.0)          revisar
2024         JALISCO      MAIZ   152247        siniestrada 152,247 ha > asegurada 41,417 ha (ratio 3.7)          revisar
2019    QUINTANA ROO      CANA   136870        siniestrada 136,870 ha > asegurada 65,542 ha (ratio 2.1)          revisar
2020    QUINTANA ROO      CANA   131504        siniestrada 131,504 ha > asegurada 83,479 ha (ratio 1.6)          revisar
2024          SONORA    ZACATE   118235        siniestrada 118,235 ha > asegurada 66,433 ha (ratio 1.8)          revisar
```
(+259 más en `hallazgos_agricola.csv`)

## B3b_siniestro_sin_emision — 196 hallazgos

```
anio         entidad       cultivo  valor                                                                                                   detalle accion_propuesta
2013 SAN LUIS POTOSI     CACAHUATE 138949 siniestrada 138,949 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2010  AGUASCALIENTES NO DISPONIBLE 100000 siniestrada 100,000 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2019 SAN LUIS POTOSI        FRIJOL  72070  siniestrada 72,070 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2009          SONORA NO DISPONIBLE  44202  siniestrada 44,202 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2008          OAXACA NO DISPONIBLE  22088  siniestrada 22,088 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2011 SAN LUIS POTOSI     AVENA EBO  21312  siniestrada 21,312 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2009         JALISCO NO DISPONIBLE  15159  siniestrada 15,159 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2009         CHIAPAS NO DISPONIBLE  10343  siniestrada 10,343 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2020 SAN LUIS POTOSI        FRIJOL   8809   siniestrada 8,809 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2009        CAMPECHE NO DISPONIBLE   8641   siniestrada 8,641 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2009       ZACATECAS NO DISPONIBLE   7070   siniestrada 7,070 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2009        TLAXCALA NO DISPONIBLE   5398   siniestrada 5,398 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2009 BAJA CALIFORNIA NO DISPONIBLE   5137   siniestrada 5,137 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2008         JALISCO NO DISPONIBLE   5084   siniestrada 5,084 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
2022  AGUASCALIENTES          MAIZ   4594   siniestrada 4,594 ha sin emisión ese año (¿ciclo previo o etiqueta de cultivo distinta entre archivos?)          revisar
```
(+181 más en `hallazgos_agricola.csv`)

## B4_pagado_mayor_suma — 109 hallazgos

```
anio         entidad         cultivo     valor                                       detalle accion_propuesta
2019 SAN LUIS POTOSI          FRIJOL 107481855         pagado 107,481,855 > suma asegurada 0          revisar
2012         TABASCO          PAPAYO  61640549    pagado 61,640,549 > suma asegurada 320,400          revisar
2016 SAN LUIS POTOSI            MAIZ  36687915  pagado 36,687,915 > suma asegurada 7,962,695          revisar
2013 SAN LUIS POTOSI       CACAHUATE  33899996          pagado 33,899,996 > suma asegurada 0          revisar
2019       CHIHUAHUA          FRIJOL  24515743  pagado 24,515,743 > suma asegurada 2,364,200          revisar
2024      NUEVO LEON          TABACO  18583323          pagado 18,583,323 > suma asegurada 0          revisar
2023       ZACATECAS          FRIJOL  15268770 pagado 15,268,770 > suma asegurada 10,420,233          revisar
2023      NUEVO LEON          TABACO  10368824          pagado 10,368,824 > suma asegurada 0          revisar
2011 SAN LUIS POTOSI       AVENA EBO  10291540          pagado 10,291,540 > suma asegurada 0          revisar
2022  AGUASCALIENTES            MAIZ   9188200           pagado 9,188,200 > suma asegurada 0          revisar
2012         JALISCO          CEBADA   8089500   pagado 8,089,500 > suma asegurada 6,137,100          revisar
2019         JALISCO           SORGO   7537996   pagado 7,537,996 > suma asegurada 2,402,000          revisar
2012         CHIAPAS          FRIJOL   6903360     pagado 6,903,360 > suma asegurada 254,555          revisar
2017       CHIHUAHUA AVENA FORRAJERA   6000000      pagado 6,000,000 > suma asegurada 30,000          revisar
2019       MICHOACAN       ZANAHORIA   5105000           pagado 5,105,000 > suma asegurada 0          revisar
```
(+94 más en `hallazgos_agricola.csv`)

## B5_salto_superficie_atipico — 433 hallazgos

```
anio         entidad      cultivo   valor                                             detalle accion_propuesta
2014       MICHOACAN         MAIZ 1372072 sup 1,372,072 ha vs mediana resto 269,232 ha (z≈14)          revisar
2019       MICHOACAN         MAIZ  924063    sup 924,063 ha vs mediana resto 269,232 ha (z≈8)          revisar
2018       CHIHUAHUA       FRIJOL  874551    sup 874,551 ha vs mediana resto 19,118 ha (z≈31)          revisar
2014       QUERETARO         MAIZ  623726    sup 623,726 ha vs mediana resto 59,522 ha (z≈12)          revisar
2018        VERACRUZ OTRO CULTIVO  590602    sup 590,602 ha vs mediana resto 277 ha (z≈1,552)          revisar
2017        VERACRUZ OTRO CULTIVO  518638    sup 518,638 ha vs mediana resto 277 ha (z≈1,363)          revisar
2014       CHIHUAHUA        AVENA  434390    sup 434,390 ha vs mediana resto 11,914 ha (z≈24)          revisar
2011         CHIAPAS        MANGO  433892     sup 433,892 ha vs mediana resto 38,861 ha (z≈9)          revisar
2019         NAYARIT        SORGO  422666    sup 422,666 ha vs mediana resto 30,638 ha (z≈12)          revisar
2013      GUANAJUATO        SORGO  409028    sup 409,028 ha vs mediana resto 23,846 ha (z≈12)          revisar
2017         NAYARIT        ARROZ  384860     sup 384,860 ha vs mediana resto 2,994 ha (z≈90)          revisar
2014      GUANAJUATO        SORGO  364877    sup 364,877 ha vs mediana resto 23,846 ha (z≈10)          revisar
2013       CHIHUAHUA        AVENA  319899    sup 319,899 ha vs mediana resto 11,914 ha (z≈18)          revisar
2015         NAYARIT         MAIZ  310245     sup 310,245 ha vs mediana resto 33,364 ha (z≈8)          revisar
2017 SAN LUIS POTOSI       FRIJOL  272948     sup 272,948 ha vs mediana resto 9,389 ha (z≈24)          revisar
```
(+418 más en `hallazgos_agricola.csv`)
