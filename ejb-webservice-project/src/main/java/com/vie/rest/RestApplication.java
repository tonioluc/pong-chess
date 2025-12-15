package com.vie.rest;

import jakarta.ws.rs.ApplicationPath;
import jakarta.ws.rs.core.Application;

/**
 * Configuration de l'application REST
 * Tous les endpoints seront disponibles sous /api/*
 */
@ApplicationPath("/api")
public class RestApplication extends Application {
    // JAX-RS va automatiquement découvrir tous les @Path
}
