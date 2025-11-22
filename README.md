<b><h2>Requerimientos antes de compilar la aplicación:</h2></b>
   <ul>
         <li>Tener instalado Python en la computadora.</li>
         <li>Contar con la URI de la base de datos</li>
         <li>Tener instalado un navegador web en la computadora.</li>
   </ul>

<b><h2>Cómo compilar la aplicación: </h2></b>
   <ol>
      <li>Instalar las dependencias necesarias (flask, flask_cors, pymongo usando pip install)</li>
      <li>Crear un archivo llamado URI.py, dentro de él debes crear una variable llamada URI cuyo valor será la URI para acceder a la base de datos (debe de ir entrecomillado)</li>
      <li>Correr el archivo app.py (python app.py)</li>
      <li>Abrir el archivo index.html dentro de la carpeta frontend en el navegador.</li>
   </ol>

<b><h2>Cómo funciona la aplicación: </h2></b>
El archivo app.py es una API Flask que contiene los endpoints de la aplicación. Maneja procesos relacionados a la base de datos de MongoDB y manejo de errores.
Dentro de la carpeta frontend se maneja toda la lógica dentro de los archivos script.js, script-articulos-categoria.js, script-articulos-tag.js; dentro de este script.js se define la URL de la API, así como mostrar mensajes y hacer peticiones al backend. Tiene funciones para mostrar, agregar y eliminar datos.




lalo
