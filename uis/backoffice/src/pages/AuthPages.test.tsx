import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import {
  changePassword,
  getAccessToken,
  getApiErrorMessage,
  login,
  requestPasswordReset,
  resetPassword,
} from "../services/authApi";
import { ChangePasswordPage } from "./ChangePasswordPage";
import { ForgotPasswordPage } from "./ForgotPasswordPage";
import { LoginPage } from "./LoginPage";
import { ResetPasswordPage } from "./ResetPasswordPage";

vi.mock("../services/authApi", () => ({
  ACCESS_TOKEN_KEY: "trackflow_access_token",
  changePassword: vi.fn(),
  getAccessToken: vi.fn(),
  getApiErrorMessage: vi.fn((_error: unknown, fallback: string) => fallback),
  login: vi.fn(),
  requestPasswordReset: vi.fn(),
  resetPassword: vi.fn(),
}));

const mockedChangePassword = vi.mocked(changePassword);
const mockedGetAccessToken = vi.mocked(getAccessToken);
const mockedLogin = vi.mocked(login);
const mockedRequestPasswordReset = vi.mocked(requestPasswordReset);
const mockedResetPassword = vi.mocked(resetPassword);

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  mockedGetAccessToken.mockReturnValue("session-token");
});

test("forgot-password muestra confirmación incluso si falla la API", async () => {
  const user = userEvent.setup();
  mockedRequestPasswordReset.mockRejectedValue(new Error("offline"));

  render(
    <MemoryRouter>
      <ForgotPasswordPage />
    </MemoryRouter>,
  );

  await user.type(screen.getByLabelText("Email"), "user@example.com");
  await user.click(screen.getByRole("button", { name: "Enviar enlace" }));

  expect(
    await screen.findByText("Si esa dirección está registrada, recibirás un enlace en breve."),
  ).toBeInTheDocument();
  expect(screen.getByLabelText("Email")).toBeDisabled();
  expect(mockedRequestPasswordReset).toHaveBeenCalledWith("user@example.com");
});

test("reset-password lee token, envía el formulario y redirige al login", async () => {
  const user = userEvent.setup();
  mockedResetPassword.mockResolvedValue({ message: "ok" });

  render(
    <MemoryRouter initialEntries={["/reset-password?token=token-from-url"]}>
      <Routes>
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/login" element={<p>Login destination</p>} />
      </Routes>
    </MemoryRouter>,
  );

  await user.type(screen.getByLabelText("Nueva contraseña"), "new-password");
  await user.type(screen.getByLabelText("Confirmar nueva contraseña"), "new-password");
  await user.click(screen.getByRole("button", { name: "Actualizar contraseña" }));

  await waitFor(() => expect(screen.getByText("Login destination")).toBeInTheDocument());
  expect(mockedResetPassword).toHaveBeenCalledWith("token-from-url", "new-password");
});

test("reset-password muestra error y enlace para solicitar otro token", async () => {
  const user = userEvent.setup();
  mockedResetPassword.mockRejectedValue(new Error("expired"));

  render(
    <MemoryRouter initialEntries={["/reset-password?token=expired-token"]}>
      <ResetPasswordPage />
    </MemoryRouter>,
  );

  await user.type(screen.getByLabelText("Nueva contraseña"), "new-password");
  await user.type(screen.getByLabelText("Confirmar nueva contraseña"), "new-password");
  await user.click(screen.getByRole("button", { name: "Actualizar contraseña" }));

  expect(await screen.findByRole("alert")).toHaveTextContent("El enlace no es válido o ha expirado.");
  expect(screen.getByRole("link", { name: "Solicitar un enlace nuevo" })).toHaveAttribute(
    "href",
    "/forgot-password",
  );
});

test("login muestra el enlace visible de recuperación", () => {
  render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  );

  expect(screen.getByRole("link", { name: "¿Olvidaste tu contraseña?" })).toHaveAttribute(
    "href",
    "/forgot-password",
  );
});

test("change-password valida coincidencia antes de llamar a la API", async () => {
  const user = userEvent.setup();

  render(<ChangePasswordPage />);

  await user.type(screen.getByLabelText("Contraseña actual"), "current-password");
  await user.type(
    document.getElementById("account-new-password") as HTMLInputElement,
    "new-password",
  );
  await user.type(
    document.getElementById("account-confirm-password") as HTMLInputElement,
    "different-password",
  );
  await user.click(screen.getByRole("button", { name: "Guardar contraseña" }));

  expect(await screen.findByRole("alert")).toHaveTextContent("Las contraseñas nuevas no coinciden.");
  expect(mockedChangePassword).not.toHaveBeenCalled();
});

test("change-password muestra confirmación tras una actualización exitosa", async () => {
  const user = userEvent.setup();
  mockedChangePassword.mockResolvedValue({ message: "La contraseña se actualizó correctamente." });

  render(<ChangePasswordPage />);

  await user.type(screen.getByLabelText("Contraseña actual"), "current-password");
  await user.type(
    document.getElementById("account-new-password") as HTMLInputElement,
    "new-password",
  );
  await user.type(
    document.getElementById("account-confirm-password") as HTMLInputElement,
    "new-password",
  );
  await user.click(screen.getByRole("button", { name: "Guardar contraseña" }));

  expect(await screen.findByRole("status")).toHaveTextContent("La contraseña se actualizó correctamente.");
  expect(mockedChangePassword).toHaveBeenCalledWith(
    "current-password",
    "new-password",
    "session-token",
  );
});

test("login guarda el token tras autenticarse", async () => {
  const user = userEvent.setup();
  mockedLogin.mockResolvedValue({ access_token: "access-token", token_type: "bearer" });

  render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  );

  await user.type(screen.getByLabelText("Email"), "user@example.com");
  await user.type(screen.getByLabelText("Contraseña"), "password");
  await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));

  await waitFor(() => expect(mockedLogin).toHaveBeenCalledWith("user@example.com", "password"));
  expect(localStorage.getItem("trackflow_access_token")).toBe("access-token");
});