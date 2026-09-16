export function renderScene(canvas, scene, options = {}) {
  if (!canvas || typeof canvas.getContext !== 'function') throw new TypeError('canvas is required');
  if (!scene || !Array.isArray(scene.live) || !Array.isArray(scene.mirror)) throw new TypeError('projected live/mirror scene is required');
  const ctx = canvas.getContext('2d');
  const width = canvas.width = Math.max(320, Math.floor(canvas.clientWidth || 800));
  const height = canvas.height = Math.max(240, Math.floor(canvas.clientHeight || 500));
  ctx.clearRect(0, 0, width, height);
  const scale = Math.min(width, height) * 0.18;
  const ox = width / 2, oy = height / 2;
  const limit = Math.min(scene.live.length, scene.mirror.length, options.maxPoints ?? 1500);

  const point = (p, solid) => {
    const x = ox + p[0] * scale;
    const y = oy - p[1] * scale;
    ctx.beginPath();
    ctx.arc(x, y, solid ? 2.6 : 2.1, 0, Math.PI * 2);
    ctx.lineWidth = solid ? 2 : 1;
    ctx.setLineDash(solid ? [] : [4, 3]);
    if (solid) ctx.fill(); else ctx.stroke();
    return [x, y];
  };

  for (let i = 0; i < limit; i++) {
    const m = point(scene.mirror[i], false);
    const l = point(scene.live[i], true);
    if (Math.hypot(l[0] - m[0], l[1] - m[1]) > 0.5) {
      ctx.setLineDash([]);
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(m[0], m[1]); ctx.lineTo(l[0], l[1]); ctx.stroke();
    }
  }
  ctx.setLineDash([]);
}

export function formatInspection(model) {
  const move = model.latestMove ? `${model.latestMove.plane} ${model.latestMove.degrees > 0 ? '+' : ''}${model.latestMove.degrees}°` : 'none';
  return [
    `Shell: ${model.shell}`,
    `Moves: ${model.actionCount}`,
    `Latest move: ${move}`,
    `Live equals mirror: ${model.comparison.equal}`,
    `Max absolute coordinate delta: ${model.comparison.maxAbsDelta}`,
    `Origin displacement: ${model.originDisplacement}`,
    `Latest-step change: ${model.latestStepChange}`,
    `Observer: yaw=${model.observer.yaw}, pitch=${model.observer.pitch}, roll=${model.observer.roll}, wPerspective=${model.observer.wPerspective}`
  ].join('\n');
}
