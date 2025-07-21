import sqlite3
import hashlib
import datetime

# -------- CLASES --------

class Rol:
    def __init__(self, nombre):
        self.nombre = nombre

class Usuario:
    def __init__(self, nombre, email, contraseña_hash, rol, fecha_registro):
        self.nombre = nombre
        self.email = email
        self.contraseña_hash = contraseña_hash
        self.rol = rol
        self.fecha_registro = fecha_registro

    def ver_datos(self):
        return f"Nombre: {self.nombre}\nEmail: {self.email}\nRol: {self.rol.nombre}\nFecha: {self.fecha_registro}"

class Vehiculo:
    def __init__(self, marca, modelo, año, precio):
        self.marca = marca
        self.modelo = modelo
        self.año = año
        self.precio = precio

    def ver_info(self):
        return f"{self.marca} {self.modelo} ({self.año}) - ${self.precio:.2f}"

# -------- BASE DE DATOS --------

def conectar():
    return sqlite3.connect("database.sqlite")

def inicializar_bd():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            contraseña TEXT NOT NULL,
            rol_id INTEGER,
            fecha_registro DATE,
            FOREIGN KEY (rol_id) REFERENCES roles(id)
        )""")
    cursor.executemany("INSERT OR IGNORE INTO roles (nombre) VALUES (?)", [("Administrador",), ("Usuario",)])
    conn.commit()
    conn.close()

# -------- GESTOR --------

class GestorSistema:
    def __init__(self):
        self.vehiculos = [
            Vehiculo("Toyota", "Hilux", 2022, 28500),
            Vehiculo("Ford", "Focus", 2020, 19500),
            Vehiculo("Renault", "Sandero", 2023, 17000)
        ]

    def _hash(self, texto):
        return hashlib.sha256(texto.encode()).hexdigest()

    def _validar_contraseña(self, contraseña):
        return len(contraseña) >= 6 and any(c.isdigit() for c in contraseña) and any(c.isalpha() for c in contraseña)

    def registrar_usuario(self):
        print("\n--- Registro ---")
        nombre = input("Nombre Completo: ")
        email = input("Email: ")
        contraseña = input("Contraseña: ")

        if not self._validar_contraseña(contraseña):
            print("❌ Contraseña inválida.")
            return

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        if cursor.fetchone():
            print("❌ Email ya registrado.")
            conn.close()
            return

        cursor.execute("SELECT id FROM roles WHERE nombre = 'Usuario'")
        rol_id = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, contraseña, rol_id, fecha_registro)
            VALUES (?, ?, ?, ?, DATE('now'))
        """, (nombre, email, self._hash(contraseña), rol_id))
        conn.commit()
        conn.close()
        print(f"\n🎉 Bienvenido/a {nombre} a Concesionaria AutoPlus, ya te encuentras registrado 🎉")

    def iniciar_sesion(self):
        print("\n--- Inicio de Sesión ---")
        email = input("Email: ")
        contraseña = input("Contraseña: ")

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.nombre, u.email, u.contraseña, r.nombre, u.fecha_registro
            FROM usuarios u JOIN roles r ON u.rol_id = r.id
            WHERE u.email = ?
        """, (email,))
        datos = cursor.fetchone()
        conn.close()

        if datos and self._hash(contraseña) == datos[2]:
            usuario = Usuario(datos[0], datos[1], datos[2], Rol(datos[3]), datos[4])
            print(f"\n🎉 ¡Hola {usuario.nombre}, ya iniciaste Sesión!  🎉")
            self.menu(usuario)
        else:
            print("❌ Credenciales inválidas.")

    def menu(self, usuario):
        if usuario.rol.nombre == "Administrador":
            self.menu_admin(usuario)
        else:
            self.menu_usuario(usuario)

    def menu_usuario(self, usuario):
        while True:
            print("\n--- MENÚ USUARIO ---")
            print("1. Ver mis datos")
            print("2. Ver vehículos")
            print("3. Salir")
            opcion = input("Opción: ")
            if opcion == "1":
                print("\n" + usuario.ver_datos())
            elif opcion == "2":
                for v in self.vehiculos:
                    print("- " + v.ver_info())
            elif opcion == "3":
                print("👋 Gracias por tu visita.")
                break
            else:
                print("⚠️ Opción inválida.")

    def menu_admin(self, usuario):
        while True:
            print("\n--- MENÚ ADMINISTRADOR ---")
            print("1. Ver todos los usuarios")
            print("2. Cambiar rol de usuario")
            print("3. Eliminar usuario")
            print("4. Ver vehículos")
            print("5. Salir")
            opcion = input("Opción: ")
            conn = conectar()
            cursor = conn.cursor()

            if opcion == "1":
                cursor.execute("""
                    SELECT u.nombre, u.email, r.nombre, u.fecha_registro
                    FROM usuarios u JOIN roles r ON u.rol_id = r.id
                """)
                for u in cursor.fetchall():
                    print(f"\nNombre: {u[0]}\nEmail: {u[1]}\nRol: {u[2]}\nFecha: {u[3]}")
            elif opcion == "2":
                email = input("Email del usuario: ")
                cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
                usuario_id = cursor.fetchone()
                if usuario_id:
                    nuevo_rol = input("Nuevo rol (Administrador/Usuario): ").capitalize()
                    cursor.execute("SELECT id FROM roles WHERE nombre = ?", (nuevo_rol,))
                    rol_id = cursor.fetchone()
                    if rol_id:
                        cursor.execute("UPDATE usuarios SET rol_id = ? WHERE email = ?", (rol_id[0], email))
                        conn.commit()
                        print("✅ Rol cambiado.")
                    else:
                        print("❌ Rol inválido.")
                else:
                    print("❌ Usuario no encontrado.")
            elif opcion == "3":
                email = input("Email a eliminar: ")
                if email == usuario.email:
                    print("❌ No puedes eliminarte a ti mismo.")
                else:
                    cursor.execute("DELETE FROM usuarios WHERE email = ?", (email,))
                    conn.commit()
                    print("✅ Usuario eliminado.")
            elif opcion == "4":
                for v in self.vehiculos:
                    print("- " + v.ver_info())
            elif opcion == "5":
                conn.close()
                break
            else:
                print("⚠️ Opción inválida.")
            conn.close()

# -------- MAIN --------

if __name__ == "__main__":
    inicializar_bd()
    gestor = GestorSistema()

    while True:
        print("\n=== Concesionaria AutoPlus ===")
        print("1. Registrarse")
        print("2. Iniciar sesión")
        print("3. Salir")
        opcion = input("Opción: ")

        if opcion == "1":
            gestor.registrar_usuario()
        elif opcion == "2":
            gestor.iniciar_sesion()
        elif opcion == "3":
            print("🚗 ¡Gracias por visitar AutoPlus! 🚗")
            break
        else:
            print("⚠️ Opción inválida.")

