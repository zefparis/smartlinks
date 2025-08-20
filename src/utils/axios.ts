import axios, { AxiosError } from "axios";
import toast from "react-hot-toast";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    let message = "Erreur inconnue";
    let status = 0;

    if (error.response) {
      status = error.response.status;
      switch (status) {
        case 400:
          message = "❌ Requête invalide (400)";
          break;
        case 401:
          message = "🔑 Non autorisé (401)";
          break;
        case 403:
          message = "🚫 Accès interdit (403)";
          break;
        case 404:
          message = "🔍 Ressource non trouvée (404)";
          break;
        case 500:
          message = "💥 Erreur serveur (500)";
          break;
        default:
          message = `⚠️ Erreur serveur (${status})`;
      }
    } else if (error.request) {
      message = "🌐 Pas de réponse du serveur (timeout ou réseau)";
    } else {
      message = `Axios: ${error.message}`;
    }

    // 🔔 Affichage toast global
    toast.error(message);

    return Promise.reject({ status, message, error });
  }
);

export default api;
