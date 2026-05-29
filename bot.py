import os
from datetime import datetime, timedelta, date  # FIX: Importación limpia y explícita
import numpy as np
import pandas as pd
import yfinance as yf         
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
import requests
import matplotlib.pyplot as plt
import time

# Forzar a matplotlib a correr en modo headless (servidor sin pantalla)
plt.switch_backend('Agg')

# ==============================================================================
# CONFIGURACIÓN DE PRODUCCIÓN
# ==============================================================================
CONFIG = {
    "assets": ["RA.MX", "WALMEX.MX", "ALSEA.MX"], 
    "dend": date.today().strftime('%Y-%m-%d'),  # FIX: Corregido para evitar el AttributeError
    "modo_pruebas": True, # Déjalo en True para verificar que lleguen todas las alertas de prueba
    "ema_f": 20,
    "ema_s": 50,
    "rsi_pr": 14,
    "rsi_buy": 55,
    "rsi_sell": 45,
    "atr_pr": 14,
    "sl_mult": 1.5,
    "tp_mult": 2.5,
    "vol_pr": 20,
    "telegram_token": os.environ.get('TELEGRAM_TOKEN'),
    "telegram_chat_id": os.environ.get('TELEGRAM_CHAT_ID')
}

# ==============================================================================
# MOTOR DEL SISTEMA
# ==============================================================================
def generar_y_guardar_grafico(df, cfg, ticker, last_index, precio_entrada=None, sl=None, tp=None):
    df_plot = df.iloc[max(0, last_index-40):last_index+2].copy()
    
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), gridspec_kw={'height_ratios': [3, 1]})
    
    ax1.plot(df_plot['Date'], df_plot['askclose'], label='Precio Cierre', color='#1f77b4', linewidth=2.5, zorder=3)
    ax1.plot(df_plot['Date'], df_plot['ema20'], label=f'EMA {cfg["ema_f"]}', color='#ff7f0e', linestyle='--')
    ax1.plot(df_plot['Date'], df_plot['ema50'], label=f'EMA {cfg["ema_s"]}', color='#2ca02c', linestyle='--')
    
    if precio_entrada is not None and sl is not None and tp is not None:
        ax1.axhline(precio_entrada, color='#7f7f7f', linestyle='-', linewidth=1.5, label=f'Entrada ({precio_entrada:.2f})')
        ax1.axhline(sl, color='#d62728', linestyle=':', linewidth=2, label=f'Stop Loss ({sl:.2f})')
        ax1.axhline(tp, color='#2ca02c', linestyle=':', linewidth=2, label=f'Take Profit ({tp:.2f})')
        ax1.axhspan(precio_entrada, tp, color='#2ca02c', alpha=0.08, label='Zona Objetivo')
        ax1.axhspan(sl, precio_entrada, color='#d62728', alpha=0.08, label='Zona Riesgo')

    ax1.set_title(f"Auditoría Visual - {ticker}", fontsize=14, fontweight='bold')
    ax1.set_ylabel('Precio')
    ax1.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.95)
    
    ax2.plot(df_plot['Date'], df_plot['rsi'], color='#9467bd', linewidth=1.8, label='RSI (14)')
    ax2.axhline(cfg['rsi_buy'], color='#d62728', linestyle=':', alpha=0.8)
    ax2.axhline(cfg['rsi_sell'], color='#1f77b4', linestyle=':', alpha=0.8)
    ax2.set_ylim(15, 85)
    ax2.set_ylabel('RSI')
    
    plt.xticks(rotation=25)
    plt.tight_layout()
    
    ruta_imagen = f'alerta_{ticker}.png'
    plt.savefig(ruta_imagen, dpi=150)
    plt.close()
    return ruta_imagen

def despachar_telegram_con_foto(token, chat_id, mensaje, ruta_foto):
    if not token or not chat_id:
        print(f"⚠️ Credenciales ausentes. Falló despacho de:\n{mensaje}")
        return
    url = f'https://api.telegram.org/bot{token}/sendPhoto'
    try:
        with open(ruta_foto, 'rb') as foto:
            payload = {'chat_id': chat_id, 'caption': mensaje, 'parse_mode': 'Markdown'}
            res = requests.post(url, data=payload, files={'photo': foto})
            print(f"📸 Telegram despachado para activo. Status: {res.status_code}")
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")

def ejecutar_escanner(cfg):
    if cfg['modo_pruebas']:
        print(f"🧪 [MODO PRUEBA] Ejecutando simulación para: {cfg['assets']}")
        for idx, ticker in enumerate(cfg['assets']):
            precio_base = 60.0 + (idx * 30.0)
            fechas_mock = [datetime.now() - timedelta(days=x) for x in range(50, -1, -1)]
            df = pd.DataFrame({'Date': fechas_mock, 'askclose': np.linspace(precio_base, precio_base*1.1, 51)})
            df['askhigh'], df['asklow'], df['Volume'] = df['askclose']+1, df['askclose']-1, 200000
            df['ema20'], df['ema50'], df['rsi'], df['atr'] = df['askclose']-1, df['askclose']-3, np.linspace(40, 56, 51), 2.0
            last_index = df.index[-2]
            p_sim = round(df['askclose'].iloc[last_index], 2)
            
            ruta = generar_y_guardar_grafico(df, cfg, ticker, last_index, p_sim, p_sim-3, p_sim+5)
            msg = f"🧪 **MODO PRUEBA: {ticker}**\n🟢 Entrada simulada por automatización en GitHub Actions."
            despachar_telegram_con_foto(cfg['telegram_token'], cfg['telegram_chat_id'], msg, ruta)
        return

    for ticker in cfg['assets']:
        try:
            dias_atras = int((cfg['ema_s'] + cfg['vol_pr'] + 10) * 7 / 5)
            dini = (datetime.strptime(cfg['dend'], "%Y-%m-%d") - timedelta(days=dias_atras)).strftime('%Y-%m-%d')
            df = yf.download(ticker, start=dini, end=cfg['dend'], auto_adjust=True, progress=False)
            
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df.rename(columns={'Open':'askopen', 'High':'askhigh', 'Low':'asklow', 'Close':'askclose'}, inplace=True)
            df.reset_index(inplace=True)

            df['ema20'] = EMAIndicator(df['askclose'].squeeze(), cfg['ema_f']).ema_indicator()
            df['ema50'] = EMAIndicator(df['askclose'].squeeze(), cfg['ema_s']).ema_indicator()
            df['rsi'] = RSIIndicator(df['askclose'].squeeze(), cfg['rsi_pr']).rsi()
            df['atr'] = AverageTrueRange(df['askhigh'].squeeze(), df['asklow'].squeeze(), df['askclose'].squeeze(), cfg['atr_pr']).average_true_range()
            df['vol_sma'] = df['Volume'].rolling(cfg['vol_pr']).mean()

            df['cond_trend'] = (df['ema20'] > df['ema50']) & (df['askclose'] > df['ema20'])
            df['cond_rsi_buy'] = (df['rsi'] >= cfg['rsi_buy']) & (df['rsi'].shift(1) < cfg['rsi_buy'])
            df['cond_vol'] = df['Volume'] > df['vol_sma']
            df['signal_long'] = df['cond_trend'] & df['cond_rsi_buy'] & df['cond_vol']
            df['exit_indicators'] = (df['rsi'] < cfg['rsi_sell']) | (df['askclose'] < df['ema20'])

            last_index = df.index[-1]
            posicion_activa, entry_idx = False, None

            for i in range(max(0, last_index - 30), last_index + 1):
                if df['signal_long'].iloc[i]: posicion_activa, entry_idx = True, i
                elif posicion_activa and df['exit_indicators'].iloc[i]: posicion_activa, entry_idx = False, None

            precio_cierre = round(df['askclose'].iloc[last_index], 4)
            fecha_str = pd.to_datetime(df['Date'].iloc[last_index]).strftime('%Y/%m/%d')

            if df['signal_long'].iloc[last_index]:
                sl = round(precio_cierre - (cfg['sl_mult'] * df['atr'].iloc[last_index]), 4)
                tp = round(precio_cierre + (cfg['tp_mult'] * df['atr'].iloc[last_index]), 4)
                ruta = generar_y_guardar_grafico(df, cfg, ticker, last_index, precio_cierre, sl, tp)
                msg = f"🟢 **COMPRA ({ticker})**\n📅 {fecha_str}\n💰 Entrada: {precio_cierre}\n🛑 SL: {sl}\n🎯 TP: {tp}"
                despachar_telegram_con_foto(cfg['telegram_token'], cfg['telegram_chat_id'], msg, ruta)
            elif posicion_activa and entry_idx is not None:
                p_entry = df['askclose'].iloc[entry_idx]
                atr_e = df['atr'].iloc[entry_idx]
                sl, tp = p_entry - (cfg['sl_mult'] * atr_e), p_entry + (cfg['tp_mult'] * atr_e)

                if precio_cierre <= sl:
                    ruta = generar_y_guardar_grafico(df, cfg, ticker, last_index, p_entry, sl, tp)
                    despachar_telegram_con_foto(cfg['telegram_token'], cfg['telegram_chat_id'], f"🔴 **HIT SL ({ticker})**\n📉 Salida: {precio_cierre}", ruta)
                elif precio_cierre >= tp:
                    ruta = generar_y_guardar_grafico(df, cfg, ticker, last_index, p_entry, sl, tp)
                    despachar_telegram_con_foto(cfg['telegram_token'], cfg['telegram_chat_id'], f"🟢 **HIT TP ({ticker})**\n📈 Salida: {precio_cierre}", ruta)
                elif df['exit_indicators'].iloc[last_index]:
                    ruta = generar_y_guardar_grafico(df, cfg, ticker, last_index, p_entry, sl, tp)
                    despachar_telegram_con_foto(cfg['telegram_token'], cfg['telegram_chat_id'], f"⚠️ **EXIT TÉCNICO ({ticker})**\n📉 Salida: {precio_cierre}", ruta)
            
            time.sleep(1)
        except Exception as e:
            print(f"🚨 Error en {ticker}: {e}")
            continue

if __name__ == "__main__":
    ejecutar_escanner(CONFIG)
