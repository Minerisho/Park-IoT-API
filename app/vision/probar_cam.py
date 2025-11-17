import cv2


def probar_camara(index: int) -> None:
    print(f"\nProbando cámara con índice {index}...")

    # En Windows, CAP_DSHOW suele evitar algunos problemas con webcams.
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print(f"No se pudo abrir la cámara {index}.")
        return

    print("Cámara abierta correctamente.")
    print("Presiona 'q' en la ventana de video para cerrar esta cámara.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("No se pudo leer frame de la cámara.")
            break

        cv2.imshow(f"Camara {index}", frame)

        # Espera 1 ms; si se presiona 'q', salir
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Cámara {index} cerrada.")


if __name__ == "__main__":
    print("Script para probar índices de cámara con OpenCV.")
    print("Escribe un índice de cámara (0, 1, 2, ...) o ENTER para salir.\n")

    while True:
        user_input = input("Índice de cámara a probar (ENTER para salir): ").strip()
        if user_input == "":
            print("Saliendo.")
            break

        try:
            cam_index = int(user_input)
        except ValueError:
            print("Por favor ingresa un número entero válido.")
            continue

        probar_camara(cam_index)
