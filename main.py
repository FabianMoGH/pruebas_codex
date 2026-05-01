import tkinter as tk
from tkinter import messagebox, ttk


def formatear_importe(importe):
    texto = f"{importe:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def parsear_importe(texto):
    texto = texto.strip().replace(" ", "")

    if not texto:
        return 0.0

    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "." in texto:
        partes = texto.split(".")
        if len(partes[-1]) == 3 and len(partes) > 1:
            texto = texto.replace(".", "")

    return float(texto)


def calcular_transferencias(personas):
    total = sum(p["importe_pagado"] for p in personas)
    total_pesos = sum(0.5 if p["menor"] else 1 for p in personas)

    if total_pesos == 0:
        return 0, 0, [], [], []

    valor_adulto = total / total_pesos
    saldos = []
    saldos_por_pagador = {}

    for indice, persona in enumerate(personas):
        peso = 0.5 if persona["menor"] else 1
        debe_pagar = valor_adulto * peso
        saldo = round(persona["importe_pagado"] - debe_pagar, 2)
        saldos.append(
            {
                "indice": indice,
                "saldo": saldo,
            }
        )
        pagador = persona["pagador"] or persona["nombre"]
        saldos_por_pagador[pagador] = round(saldos_por_pagador.get(pagador, 0) + saldo, 2)

    deudores = []
    acreedores = []

    for pagador, saldo in saldos_por_pagador.items():
        if saldo < 0:
            deudores.append([pagador, -saldo])
        elif saldo > 0:
            acreedores.append([pagador, saldo])

    transferencias = []
    i = 0
    j = 0

    while i < len(deudores) and j < len(acreedores):
        deudor_pagador, debe = deudores[i]
        acreedor_pagador, cobra = acreedores[j]

        monto = min(debe, cobra)
        transferencias.append((deudor_pagador, acreedor_pagador, round(monto, 2)))

        deudores[i][1] -= monto
        acreedores[j][1] -= monto

        if deudores[i][1] < 0.01:
            i += 1
        if acreedores[j][1] < 0.01:
            j += 1

    saldos_pagadores = [
        {"pagador": pagador, "saldo": saldo}
        for pagador, saldo in saldos_por_pagador.items()
    ]

    return total, valor_adulto, saldos, saldos_pagadores, transferencias


class RepartidorGastosApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Repartidor de gastos")
        self.geometry("860x600")
        self.minsize(760, 520)

        self.personas = []

        self._crear_interfaz()

    def _crear_interfaz(self):
        contenedor = ttk.Frame(self, padding=16)
        contenedor.pack(fill="both", expand=True)

        titulo = ttk.Label(
            contenedor,
            text="Repartidor de gastos",
            font=("Segoe UI", 18, "bold"),
        )
        titulo.pack(anchor="w")

        formulario = ttk.LabelFrame(contenedor, text="Agregar persona", padding=12)
        formulario.pack(fill="x", pady=(14, 10))
        formulario.columnconfigure(1, weight=1)

        ttk.Label(formulario, text="Nombre").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.nombre_var = tk.StringVar()
        nombre_entry = ttk.Entry(formulario, textvariable=self.nombre_var)
        nombre_entry.grid(row=0, column=1, sticky="ew")

        ttk.Label(formulario, text="Alias de pago").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.alias_var = tk.StringVar()
        alias_entry = ttk.Entry(formulario, textvariable=self.alias_var)
        alias_entry.grid(row=1, column=1, sticky="ew", pady=(8, 0))

        ttk.Label(formulario, text="Importe pagado").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.pagado_var = tk.StringVar(value="0.00")
        pagado_entry = ttk.Entry(formulario, textvariable=self.pagado_var)
        pagado_entry.grid(row=2, column=1, sticky="ew", pady=(8, 0))

        ttk.Label(formulario, text="Pagador").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.pagador_var = tk.StringVar()
        self.pagador_combo = ttk.Combobox(formulario, textvariable=self.pagador_var)
        self.pagador_combo.grid(row=3, column=1, sticky="ew", pady=(8, 0))

        self.menor_var = tk.BooleanVar()
        menor_check = ttk.Checkbutton(formulario, text="Es menor de edad", variable=self.menor_var)
        menor_check.grid(row=4, column=1, sticky="w", pady=(8, 0))

        botones_form = ttk.Frame(formulario)
        botones_form.grid(row=5, column=1, sticky="e", pady=(12, 0))

        agregar_btn = ttk.Button(botones_form, text="Agregar", command=self.agregar_persona)
        agregar_btn.pack(side="left", padx=(0, 8))

        limpiar_btn = ttk.Button(botones_form, text="Limpiar lista", command=self.limpiar_personas)
        limpiar_btn.pack(side="left")

        cuerpo = ttk.Frame(contenedor)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        listado_frame = ttk.LabelFrame(cuerpo, text="Personas", padding=10)
        listado_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        listado_frame.rowconfigure(0, weight=1)
        listado_frame.columnconfigure(0, weight=1)

        columnas = ("nombre", "alias", "tipo", "pagador", "pagado")
        self.tabla = ttk.Treeview(listado_frame, columns=columnas, show="headings", height=10)
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("alias", text="Alias")
        self.tabla.heading("tipo", text="Tipo")
        self.tabla.heading("pagador", text="Pagador")
        self.tabla.heading("pagado", text="Pagado")
        self.tabla.column("nombre", width=120)
        self.tabla.column("alias", width=120)
        self.tabla.column("tipo", width=75, anchor="center")
        self.tabla.column("pagador", width=120)
        self.tabla.column("pagado", width=95, anchor="e")
        self.tabla.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(listado_frame, orient="vertical", command=self.tabla.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tabla.configure(yscrollcommand=scrollbar.set)

        botones_listado = ttk.Frame(listado_frame)
        botones_listado.grid(row=1, column=0, columnspan=2, sticky="e", pady=(8, 0))

        borrar_btn = ttk.Button(botones_listado, text="Quitar seleccionado", command=self.quitar_seleccionado)
        borrar_btn.pack(side="left", padx=(0, 8))

        self.ejecutar_btn = ttk.Button(
            botones_listado,
            text="Ejecutar calculo",
            command=self.calcular,
            state="disabled",
        )
        self.ejecutar_btn.pack(side="left")

        resultado_frame = ttk.LabelFrame(cuerpo, text="Resultado", padding=10)
        resultado_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        resultado_frame.rowconfigure(0, weight=1)
        resultado_frame.columnconfigure(0, weight=1)

        self.resultado_text = tk.Text(resultado_frame, height=12, wrap="word", state="disabled")
        self.resultado_text.grid(row=0, column=0, sticky="nsew")
        self.resultado_text.tag_configure("menor", foreground="#c62828")

        resultado_scroll = ttk.Scrollbar(resultado_frame, orient="vertical", command=self.resultado_text.yview)
        resultado_scroll.grid(row=0, column=1, sticky="ns")
        self.resultado_text.configure(yscrollcommand=resultado_scroll.set)

        nombre_entry.focus()
        self.bind("<Return>", lambda _event: self.agregar_persona())

    def agregar_persona(self):
        nombre = self.nombre_var.get().strip()
        alias = self.alias_var.get().strip()
        pagado_texto = self.pagado_var.get().strip()
        pagador = self.pagador_var.get().strip() or nombre

        if not nombre:
            messagebox.showwarning("Dato faltante", "Ingresa el nombre de la persona.")
            return

        nombres_cargados = [persona["nombre"] for persona in self.personas]

        if nombre in nombres_cargados:
            messagebox.showwarning("Dato invalido", "Ya existe una persona con ese nombre.")
            return

        try:
            pagado = parsear_importe(pagado_texto)
        except ValueError:
            messagebox.showwarning("Dato invalido", "Ingresa un importe valido.")
            return

        if pagado < 0:
            messagebox.showwarning("Dato invalido", "El importe no puede ser negativo.")
            return

        if pagado > 0 and not alias:
            messagebox.showwarning("Dato faltante", "Ingresa el alias de pago de la persona.")
            return

        if pagador != nombre and pagador not in nombres_cargados:
            messagebox.showwarning("Dato invalido", "El pagador debe estar cargado en la lista o quedar vacio.")
            return

        persona = {
            "nombre": nombre,
            "alias": alias,
            "menor": self.menor_var.get(),
            "importe_pagado": pagado,
            "pagador": pagador,
        }
        self.personas.append(persona)
        self.tabla.insert(
            "",
            "end",
            values=(
                persona["nombre"],
                self._alias_visible(persona),
                "Menor" if persona["menor"] else "Adulto",
                persona["pagador"],
                formatear_importe(persona["importe_pagado"]),
            ),
        )

        self.nombre_var.set("")
        self.alias_var.set("")
        self.pagado_var.set("0.00")
        self.pagador_var.set("")
        self.menor_var.set(False)
        self._actualizar_pagadores()
        self._actualizar_estado_ejecucion()

    def quitar_seleccionado(self):
        seleccionado = self.tabla.selection()
        if not seleccionado:
            return

        item = seleccionado[0]
        indice = self.tabla.index(item)
        self.tabla.delete(item)
        del self.personas[indice]
        self._reparar_pagadores_eliminados()
        self._recargar_tabla()
        self._actualizar_pagadores()
        self._actualizar_estado_ejecucion()

    def limpiar_personas(self):
        self.personas.clear()
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        self._mostrar_resultado("")
        self.pagador_var.set("")
        self._actualizar_pagadores()
        self._actualizar_estado_ejecucion()

    def calcular(self):
        if not self.personas:
            messagebox.showwarning("Sin personas", "Agrega al menos una persona para calcular.")
            return

        total, valor_adulto, saldos, saldos_pagadores, transferencias = calcular_transferencias(self.personas)
        personas_por_nombre = {persona["nombre"]: persona for persona in self.personas}
        saldos_por_indice = {
            saldo_persona["indice"]: saldo_persona["saldo"]
            for saldo_persona in saldos
        }

        lineas = [
            (f"TOTAL GASTADO: {formatear_importe(total)}", False),
            (f"VALOR ADULTO: {formatear_importe(valor_adulto)}", False),
            (f"VALOR MENOR: {formatear_importe(valor_adulto * 0.5)}", True),
            ("", False),
            ("SALDOS:", False),
        ]

        for saldo_pagador in saldos_pagadores:
            pagador = saldo_pagador["pagador"]
            saldo = saldo_pagador["saldo"]
            persona_pagadora = personas_por_nombre.get(pagador)
            es_menor = bool(persona_pagadora and persona_pagadora["menor"])
            alias = self._alias_visible(persona_pagadora)
            lineas.append((self._linea_saldo(pagador, alias, saldo), es_menor))

            for indice, persona in enumerate(self.personas):
                if persona["pagador"] != pagador or persona["nombre"] == pagador:
                    continue

                saldo_individual = saldos_por_indice[indice]
                alias_individual = self._alias_visible(persona)
                linea = self._linea_saldo(
                    persona["nombre"],
                    alias_individual,
                    saldo_individual,
                    prefijo="\t",
                    sufijo=f" - paga {pagador}",
                )
                lineas.append((linea, persona["menor"]))

            lineas.append(("", False))

        lineas.append(("TRANSFERENCIAS ENTRE PAGADORES:", False))

        if not transferencias:
            lineas.append(("No hace falta transferir nada.", False))
        else:
            for deudor_pagador, acreedor_pagador, monto in transferencias:
                deudor = personas_por_nombre.get(deudor_pagador)
                acreedor = personas_por_nombre.get(acreedor_pagador)
                alias_acreedor = self._alias_visible(acreedor)
                es_menor = bool((deudor and deudor["menor"]) or (acreedor and acreedor["menor"]))
                lineas.append(
                    (
                        f"{deudor_pagador} transfiere {formatear_importe(monto)} "
                        f"a {acreedor_pagador} (alias: {alias_acreedor})",
                        es_menor,
                    )
                )

        self._mostrar_resultado(lineas)

    def _mostrar_resultado(self, lineas):
        self.resultado_text.configure(state="normal")
        self.resultado_text.delete("1.0", "end")

        if isinstance(lineas, str):
            self.resultado_text.insert("1.0", lineas)
        else:
            for texto, es_menor in lineas:
                etiqueta = ("menor",) if es_menor else ()
                self.resultado_text.insert("end", f"{texto}\n", etiqueta)

        self.resultado_text.configure(state="disabled")

    def _actualizar_estado_ejecucion(self):
        estado = "normal" if self.personas else "disabled"
        self.ejecutar_btn.configure(state=estado)

    def _alias_visible(self, persona):
        if not persona:
            return "x"

        return persona["alias"] or "x"

    def _linea_saldo(self, nombre, alias, saldo, prefijo="", sufijo=""):
        persona = f"{nombre} ({alias})"

        if saldo > 0:
            texto_saldo = f"debe cobrar {formatear_importe(saldo)}"
        elif saldo < 0:
            texto_saldo = f"debe pagar {formatear_importe(-saldo)}"
        else:
            texto_saldo = "está hecho"

        return f"{prefijo}{persona} {texto_saldo}{sufijo}"

    def _actualizar_pagadores(self):
        self.pagador_combo["values"] = [persona["nombre"] for persona in self.personas]

    def _reparar_pagadores_eliminados(self):
        nombres = {persona["nombre"] for persona in self.personas}

        for persona in self.personas:
            if persona["pagador"] not in nombres:
                persona["pagador"] = persona["nombre"]

    def _recargar_tabla(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        for persona in self.personas:
            self.tabla.insert(
                "",
                "end",
                values=(
                    persona["nombre"],
                    self._alias_visible(persona),
                    "Menor" if persona["menor"] else "Adulto",
                    persona["pagador"],
                    formatear_importe(persona["importe_pagado"]),
                ),
            )


if __name__ == "__main__":
    app = RepartidorGastosApp()
    app.mainloop()
