// pm2 process file (Linux server). Create the venv first: python -m venv .venv
module.exports = {
  apps: [
    {
      name: 'portfolio-api',
      script: '.venv/bin/gunicorn',
      args: '-w 2 -b 127.0.0.1:5340 wsgi:app',
      interpreter: 'none',
      cwd: __dirname,
    },
  ],
};
