@echo off
echo 🚀 Iniciando deployment...

echo 📦 Activando entorno virtual...
call venv\Scripts\activate

echo 📚 Instalando dependencias...
pip install -r requirements.txt

echo 🗄️ Ejecutando migraciones...
python manage.py migrate

echo 📁 Recopilando archivos estáticos...
python manage.py collectstatic --noinput

echo 👤 Configurando datos iniciales...
python manage.py setup_initial_data

echo ✅ Deployment completado!
echo 🌐 Servidor listo para iniciar con: python manage.py runserver
pause