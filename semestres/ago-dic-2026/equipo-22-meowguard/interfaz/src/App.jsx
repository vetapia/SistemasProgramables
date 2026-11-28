import { useEffect, useState } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, onAuthStateChanged, signInWithEmailAndPassword, signOut } from 'firebase/auth';
import { getDatabase, limitToLast, onValue, orderByChild, query, ref } from 'firebase/database';

const env = import.meta.env;
const config = {
  apiKey: env.VITE_FIREBASE_API_KEY || 'TU_API_KEY',
  authDomain: env.VITE_FIREBASE_AUTH_DOMAIN || '',
  databaseURL: env.VITE_FIREBASE_DATABASE_URL || '',
  projectId: env.VITE_FIREBASE_PROJECT_ID || '',
  appId: env.VITE_FIREBASE_APP_ID || '',
};
let auth;
let db;
if (Object.values(config).every((value) => value && !value.includes('TU_'))) {
  const app = initializeApp(config);
  auth = getAuth(app);
  db = getDatabase(app);
}

const date = new Intl.DateTimeFormat('es-MX', {dateStyle: 'medium', timeStyle: 'medium'});
const formatDate = (ts) => ts ? date.format(new Date(ts)) : '—';
const withUnit = (value, unit) => Number.isFinite(value) ? `${value} ${unit}` : '—';
const direction = {s: 'Detenido', f: 'Avance', b: 'Reversa', l: 'Izquierda', r: 'Derecha'};

function Login() {
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);

  async function submit(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setSending(true);
    setMessage('');
    try {
      await signInWithEmailAndPassword(auth, data.get('email'), data.get('password'));
    } catch {
      setMessage('No se pudo iniciar sesión. Revisa tus datos y el acceso a Firebase.');
    } finally {
      setSending(false);
    }
  }

  return <form className="panel login" onSubmit={submit}>
    <h2>Iniciar sesión</h2>
    <label>Correo electrónico<input name="email" type="email" autoComplete="username" required /></label>
    <label>Contraseña<input name="password" type="password" autoComplete="current-password" required /></label>
    <button disabled={sending}>{sending ? 'Ingresando…' : 'Entrar'}</button>
    {message && <p role="alert">{message}</p>}
  </form>;
}

function Monitor() {
  const [telemetry, setTelemetry] = useState(null);
  const [detections, setDetections] = useState(null);
  const [errors, setErrors] = useState({});
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 2000);
    const failed = (key) => () => setErrors((old) => ({...old, [key]: true}));
    const clear = (key) => setErrors((old) => ({...old, [key]: false}));
    const stopTelemetry = onValue(ref(db, 'meowguard/telemetry/latest'), (snapshot) => {
      setTelemetry(snapshot.val());
      clear('telemetry');
    }, failed('telemetry'));
    const recent = query(ref(db, 'meowguard/detections'), orderByChild('ts_ms'), limitToLast(30));
    const stopDetections = onValue(recent, (snapshot) => {
      const rows = [];
      snapshot.forEach((child) => { rows.push({key: child.key, ...child.val()}); });
      setDetections(rows.reverse());
      clear('detections');
    }, failed('detections'));
    return () => { clearInterval(timer); stopTelemetry(); stopDetections(); };
  }, []);

  const current = telemetry?.ts_ms && now - telemetry.ts_ms < 15000;
  const motion = telemetry && direction[telemetry.motion];
  const alert = telemetry?.wheel_alert;
  const traction = alert
    ? `${alert.wheel} · ${alert.reason === 'giro_excesivo' ? 'Giro excesivo' : 'Rueda lenta'}`
    : telemetry?.drift ? 'Desvío de rumbo' : telemetry ? 'Sin alertas' : '—';

  return <>
    <section aria-labelledby="telemetria">
      <div className="section-head"><h2 id="telemetria">Telemetría</h2>
        <span className={current ? 'live' : 'muted'}>{current ? 'Actualizada' : 'Sin datos recientes'}</span>
      </div>
      {errors.telemetry && <p role="alert">Acceso a telemetría denegado. Revisa los permisos de la cuenta.</p>}
      <dl className="grid">
        <div className="panel"><dt>Movimiento</dt><dd>{motion || '—'}</dd><p>{telemetry?.mode === 'auto' ? 'Automático' : telemetry ? 'Manual' : '—'}</p></div>
        <div className="panel"><dt>Obstáculo al frente</dt><dd>{withUnit(telemetry?.front, 'cm')}</dd><p>Sensor trasero {telemetry ? (telemetry.rear ? 'ocupado' : 'libre') : '—'}</p></div>
        <div className="panel"><dt>PWM por lado</dt><dd>{withUnit(telemetry?.pwm_left, '%')} / {withUnit(telemetry?.pwm_right, '%')}</dd><p>Izquierda / derecha</p></div>
        <div className="panel"><dt>Tracción</dt><dd className="small">{traction}</dd><p>{withUnit(telemetry?.yaw_dps, '°/s')}</p></div>
      </dl>
      <p className="muted">Última lectura {formatDate(telemetry?.ts_ms)}</p>
    </section>
    <section aria-labelledby="detecciones">
      <div className="section-head"><h2 id="detecciones">Detecciones recientes</h2></div>
      <div className="panel table">
        {errors.detections ? <p role="alert">Acceso a detecciones denegado.</p>
          : !detections?.length ? <p>{detections === null ? 'Cargando…' : 'Aún no hay detecciones registradas.'}</p>
          : <table><thead><tr><th>Clase</th><th>Confianza</th><th>Fecha y hora</th></tr></thead><tbody>
            {detections.map((row) => <tr key={row.key}><td>{row.label}</td>
              <td>{Number.isFinite(row.confidence) ? `${Math.round(row.confidence * 100)} %` : '—'}</td>
              <td>{formatDate(row.ts_ms)}</td></tr>)}
          </tbody></table>}
      </div>
    </section>
  </>;
}

export default function App() {
  const [user, setUser] = useState(undefined);
  useEffect(() => auth ? onAuthStateChanged(auth, setUser) : undefined, []);
  return <>
    <header><div className="wrap nav"><div><p>Equipo 22</p><h1>Meowguard</h1></div>
      {user && <button onClick={() => signOut(auth)}>Cerrar sesión</button>}
    </div></header>
    <main className="wrap">
      {!auth ? <div className="panel"><h2>Conexión pendiente</h2><p>Configura Firebase en <code>interfaz/.env</code> y reinicia Vite.</p></div>
        : user === undefined ? <p role="status">Conectando…</p>
        : user ? <Monitor /> : <Login />}
    </main>
  </>;
}
