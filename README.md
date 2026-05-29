# KinichBot
Repositorio y vehículo de despliegue para el KinichBot

## Escáner Automatizado de Tendencias - Mercado de Capitales (BMV)

Este sistema es una herramienta de soporte cuantitativo para la toma de decisiones financieras. Su objetivo es escanear diariamente un portafolio seleccionado de acciones (por defecto en la Bolsa Mexicana de Valores) al cierre del mercado, identificando oportunidades de **continuación de tendencia** y generando alertas de gestión de riesgo personalizadas.

El sistema funciona de manera 100% autónoma en la nube, despachando informes técnicos detallados directamente a Telegram sin necesidad de infraestructura local o intervención humana diaria.

---

### 📈 Lógica de Inversión (Estrategia Cuantitativa)

A diferencia de los modelos tradicionales de reversión a la media (comprar barato/sobreventa), este algoritmo está diseñado para **Trend Following** (seguimiento de tendencia). Busca incorporarse a movimientos institucionales con fuerte impulso alcista para capturar tramos largos de rendimiento.

El bot valida tres filtros concurrentes antes de emitir una señal de **Compra (Entrada LONG)**:

1. **Filtro de Tendencia Estructural (EMAs):** El precio de cierre debe cotizar por encima de la Media Móvil Exponencial de 20 periodos (**EMA 20**), y esta a su vez debe estar por encima de la **EMA 50**. Esto asegura que solo se opera a favor de la marea macro del mercado.
2. **Gatillo de Impulso (RSI de Continuación):** Evaluado en un horizonte estándar de 14 periodos. La señal se activa estrictamente cuando el **RSI cruza al alza el nivel de 55**. Este umbral matemático identifica el momento exacto en que la acción entra en una fase de aceleración alcista, evitando el "ruido" de los mercados laterales.
3. **Confirmación de Volumen Institucional:** El volumen transaccionado en la última sesión debe ser superior al promedio móvil de volumen de las últimas 20 velas. Esto valida que el movimiento del precio está respaldado por flujos de capital real y no por volatilidad minorista.

---

### 🛡️ Gestión de Riesgo Dinámica (Modelado ATR)

El bot no utiliza órdenes de salida fijas o porcentuales arbitrarias. En su lugar, lee la volatilidad histórica reciente de cada activo individual utilizando el **Average True Range (ATR de 14 periodos)** para estructurar el espacio del trade:

* **Stop Loss (Límite de Pérdida Tolerable):** Configurado a **1.5 veces el ATR** por debajo del precio de entrada. Esto protege la posición adaptándose al "ruido" natural y la liquidez específica de la acción.
* **Take Profit (Objetivo de Retorno esperado):** Configurado a **2.5 veces el ATR** por encima del precio de entrada, estableciendo una **Relación Riesgo/Beneficio óptima de 1:1.66**.

---

### 🔄 Funcionamiento del Workflow e Implicaciones Operativas

El comportamiento y la automatización de este sistema conllevan las siguientes características operativas:

* **Ejecución Programada Autónoma:** El algoritmo se ejecuta de forma automática en los servidores de GitHub de **lunes a viernes a las 3:01 PM (Hora CDMX)**. Corre inmediatamente después del cierre de la BMV para garantizar que los datos de la última vela diaria estén completamente firmados y consolidados.
* **Alertas Visuales de Auditoría:** Si el mercado activa una señal, recibirás un mensaje de Telegram con los niveles matemáticos exactos (Entrada, SL, TP) junto con un gráfico técnico aclaratorio. El gráfico delimita con franjas sombreadas el canal de riesgo (rojo) y beneficio (verde) proyectado.
* **Seguimiento de Posiciones Abiertas:** El bot mantiene un registro virtual de los activos que dieron entrada en las últimas 30 sesiones. Evaluará diariamente si el precio de cierre cruzó el Stop Loss o el Take Profit por ATR, o si ocurrió una **Salida Técnica** (RSI cayendo por debajo de 45 o precio rompiendo a la baja la EMA 20).
* **Filtro contra Fallos de Mercado:** Las acciones de la BMV pueden presentar anomalías de datos o suspensiones de cotización. El flujo está blindado para procesar cada activo en un contenedor aislado; si un ticker falla o no presenta datos, el sistema lo descarta del reporte diario pero continúa analizando el resto de la cartera.

---

### ⚠️ Consideraciones de Uso Financiero

* **Soft Signals (Señales de Alerta):** Las notificaciones enviadas por este bot deben tratarse como señales indicativas de alta probabilidad técnica. Se requiere un análisis fundamental y de liquidez posterior antes de realizar la ejecución manual en la mesa de dinero.
* **Riesgo de Deslizamiento (Slippage):** Dado que el análisis se realiza al cierre del mercado diario, las órdenes de entrada sugeridas corresponden al precio de clausura de la sesión. La ejecución real a la mañana siguiente en la apertura puede sufrir variaciones debido a *gaps* de mercado o spreads amplios en activos de mediana o baja capitalización.
