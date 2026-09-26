import tkinter as tk
from tkinter import messagebox
import security
import autostart

def ask_credentials():
    """
    Abre uma interface limpa para configurar as credenciais e a inicialização automática.
    """
    root = tk.Tk()
    root.title("Acesso Rápido Wi-Fi - UEMA")
    root.geometry("380x330")
    root.eval('tk::PlaceWindow . center')
    root.configure(padx=20, pady=20)
    root.resizable(False, False)

    tk.Label(root, text="Automação Wi-Fi UEMA", font=("Segoe UI", 13, "bold"), fg="#1e526f").pack(pady=(0, 5))
    tk.Label(
        root,
        text="Suas credenciais serão salvas de forma criptografada\nno Cofre do Windows (Credential Locker).",
        font=("Segoe UI", 9),
        fg="#52616a"
    ).pack(pady=(0, 8))

    tk.Label(
        root,
        text="⚠ O portal da UEMA usa HTTP sem criptografia no envio.\nEvite redes Wi-Fi suspeitas.",
        font=("Segoe UI", 8),
        fg="#a03030"
    ).pack(pady=(0, 10))

    tk.Label(root, text="Matrícula / Usuário SIGUEMA:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
    user_entry = tk.Entry(root, width=35, font=("Segoe UI", 10))
    user_entry.pack(fill="x", pady=(2, 10))

    # Preenche se já existir
    saved_user, _ = security.get_credentials()
    if saved_user:
        user_entry.insert(0, saved_user)

    tk.Label(root, text="Senha SIGUEMA:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
    pass_entry = tk.Entry(root, show="*", width=35, font=("Segoe UI", 10))
    pass_entry.pack(fill="x", pady=(2, 4))

    show_pass_var = tk.BooleanVar(value=False)

    def toggle_password():
        pass_entry.config(show="" if show_pass_var.get() else "*")

    tk.Checkbutton(
        root,
        text="Mostrar senha",
        variable=show_pass_var,
        command=toggle_password,
        font=("Segoe UI", 9)
    ).pack(anchor="w", pady=(0, 10))

    autostart_var = tk.BooleanVar(value=True)
    autostart_chk = tk.Checkbutton(
        root,
        text="Iniciar automaticamente com o Windows (Recomendado)",
        variable=autostart_var,
        font=("Segoe UI", 9)
    )
    autostart_chk.pack(anchor="w", pady=(0, 15))

    def save():
        u = user_entry.get().strip()
        p = pass_entry.get().strip()
        if not u or not p:
            messagebox.showwarning("Campos Obrigatórios", "Por favor, preencha o usuário e a senha.")
            return

        success = security.save_credentials(u, p)
        if success:
            if autostart_var.get():
                autostart.set_autostart(True)
            messagebox.showinfo(
                "Configuração Concluída",
                "Credenciais salvas com segurança!\nO aplicativo ficará ativo em segundo plano."
            )
            root.destroy()
        else:
            messagebox.showerror("Erro", "Não foi possível acessar o cofre de credenciais.")

    btn = tk.Button(
        root,
        text="Salvar e Ativar",
        command=save,
        bg="#276489",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        cursor="hand2",
        relief="flat",
        height=2
    )
    btn.pack(fill="x")

    def clear_saved():
        if security.delete_credentials():
            user_entry.delete(0, tk.END)
            pass_entry.delete(0, tk.END)
            messagebox.showinfo("Credenciais Removidas", "Usuário e senha apagados do Cofre do Windows.")
        else:
            messagebox.showerror("Erro", "Não foi possível remover as credenciais.")

    tk.Button(
        root,
        text="Apagar credenciais salvas",
        command=clear_saved,
        font=("Segoe UI", 8, "underline"),
        fg="#a03030",
        relief="flat",
        cursor="hand2",
        borderwidth=0,
        highlightthickness=0
    ).pack(pady=(8, 0))

    root.bind('<Return>', lambda _event: save())

    root.lift()
    # Sem '-topmost': não rouba o foco de outras janelas do usuário
    root.mainloop()

if __name__ == "__main__":
    ask_credentials()
