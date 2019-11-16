# **Projects**

Repo de proyectos que quiera implementar. Por el momento:

**Completados**

- Web API Glucosa
- Pagina web: *para portfolio / mostrar proyectos (Casi terminada)*

**En progreso:**

- Android APP: *Loguear gluscosa etc en dispositivos mobiles android y sincronizarlos con los datos de la web API*

**Futuros proyectos:**

Construir algun modelo de redes neuronales para resolver alguno de los siguientes problemas:

- Tomar mis valores de glucosa y uso de insulina y construir una red neuronal que ayude a predecir las dosis de insulina necesarias en un cualquier momento dado, o predicciones relacionadas con la ingesta de comida (en terminos de carbohidratos) para lograr niveles estables de glucosa en sangre.

- **Deteccion de cheats en Counter-Strike GO**. CS:GO es un shooter competitivo en primera persona. En la actualidad existen programas o 'cheats' que son creados y comercializados a jugadores del mismo. Estos programas crean ventajas injustas porque otorgan, a aquellos que los utilizan, presicion de disparo y velocidad de reaccion inhumanas; o la posibilidad de ver la posicion de un jugador enemigo cuando no deberia ser posible, por ejemplo si este se encuentra detras de una pared o cubierto por una cortina de humo.

> **Deteccion**

> Los desarrolladores de juegos cuentan con sistemas para detectar alguno de estos 'cheats' y asi poder eliminar a aquellos jugadores tramposos, pero se basan en detectar cambios introducidos externamente al Cliente de cada jugador. Como resultado, tanto el desarrollador del juego como los programadores de estos 'cheats' deben actualizar permanentemente sus productos para detectar o evitar ser detectados.

> Otra manera posible de deteccion (llamda Overwatch) existente consiste en guardar cada una de las partidas en donde algun jugador halla reportado actividades sospechosas de otro juegador (archivo formato .dem). Dicho 'Replay' de la partida sera revisado para varios Inspectores de la comunidad y votaran, de forma individual, si el jugador sospechoso es inocente, cupable, o inconcluso.

**Modelo**

La idea entonces es tomar todos estos 'Replays' con sus respectivas decisiones y entrenar una red neuronal que analice cada frame de la partida y, mediante el comportamiento del jugador (por ejemplo si apunta perfectamente atraves de humo), devuelva la probabilidad que est'e haciendo trampa.
