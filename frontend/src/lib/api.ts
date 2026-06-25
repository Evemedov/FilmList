import axios from "axios";
import { toast } from "@/hooks/use-toast";

export const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = "An unexpected error occurred";
    
    if (error.response) {
      if (error.response.data && error.response.data.detail) {
        const detail = error.response.data.detail;
        message = Array.isArray(detail) ? detail[0].msg : detail;
      } else {
        message = `Server error: ${error.response.status}`;
      }
    } else if (error.request) {
      message = "Network error. The backend might be down.";
    }

    toast({
      variant: "destructive",
      title: "Error",
      description: message,
    });

    return Promise.reject(error);
  }
);
