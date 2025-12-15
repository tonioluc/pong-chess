package com.vie.rest;

import com.vie.entity.Vie;
import com.vie.service.VieServiceRemote;
import jakarta.ejb.EJB;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.util.List;

/**
 * API REST pour la gestion des Vies
 * Endpoints JSON pour CRUD complet
 */
@Path("/vies")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class VieRestController {

    @EJB
    private VieServiceRemote vieService;

    /**
     * GET /api/vies - Récupérer toutes les vies
     */
    @GET
    public Response getAllVies() {
        try {
            List<Vie> vies = vieService.findAll();
            return Response.ok(vies).build();
        } catch (Exception e) {
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity(new ErrorResponse("Erreur lors de la récupération des vies: " + e.getMessage()))
                    .build();
        }
    }

    /**
     * GET /api/vies/{id} - Récupérer une vie par ID
     */
    @GET
    @Path("/{id}")
    public Response getVieById(@PathParam("id") Long id) {
        try {
            Vie vie = vieService.findById(id);
            if (vie == null) {
                return Response.status(Response.Status.NOT_FOUND)
                        .entity(new ErrorResponse("Vie non trouvée avec l'ID: " + id))
                        .build();
            }
            return Response.ok(vie).build();
        } catch (Exception e) {
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity(new ErrorResponse("Erreur lors de la récupération de la vie: " + e.getMessage()))
                    .build();
        }
    }

    /**
     * POST /api/vies - Créer une nouvelle vie
     */
    @POST
    public Response createVie(Vie vie) {
        try {
            if (vie.getLibelle() == null || vie.getLibelle().trim().isEmpty()) {
                return Response.status(Response.Status.BAD_REQUEST)
                        .entity(new ErrorResponse("Le libellé est obligatoire"))
                        .build();
            }
            
            Vie createdVie = vieService.create(vie);
            return Response.status(Response.Status.CREATED)
                    .entity(createdVie)
                    .build();
        } catch (Exception e) {
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity(new ErrorResponse("Erreur lors de la création de la vie: " + e.getMessage()))
                    .build();
        }
    }

    /**
     * PUT /api/vies/{id} - Mettre à jour une vie
     */
    @PUT
    @Path("/{id}")
    public Response updateVie(@PathParam("id") Long id, Vie vie) {
        try {
            if (vie.getLibelle() == null || vie.getLibelle().trim().isEmpty()) {
                return Response.status(Response.Status.BAD_REQUEST)
                        .entity(new ErrorResponse("Le libellé est obligatoire"))
                        .build();
            }
            
            vie.setLid(id);
            Vie updatedVie = vieService.update(vie);
            return Response.ok(updatedVie).build();
        } catch (RuntimeException e) {
            if (e.getMessage().contains("not found")) {
                return Response.status(Response.Status.NOT_FOUND)
                        .entity(new ErrorResponse("Vie non trouvée avec l'ID: " + id))
                        .build();
            }
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity(new ErrorResponse("Erreur lors de la mise à jour de la vie: " + e.getMessage()))
                    .build();
        }
    }

    /**
     * DELETE /api/vies/{id} - Supprimer une vie
     */
    @DELETE
    @Path("/{id}")
    public Response deleteVie(@PathParam("id") Long id) {
        try {
            boolean deleted = vieService.delete(id);
            if (!deleted) {
                return Response.status(Response.Status.NOT_FOUND)
                        .entity(new ErrorResponse("Vie non trouvée avec l'ID: " + id))
                        .build();
            }
            return Response.ok(new SuccessResponse("Vie supprimée avec succès lesy a")).build();
        } catch (Exception e) {
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity(new ErrorResponse("Erreur lors de la suppression de la vie: " + e.getMessage()))
                    .build();
        }
    }

    /**
     * GET /api/vies/count - Compter le nombre de vies
     */
    @GET
    @Path("/count")
    public Response countVies() {
        try {
            long count = vieService.count();
            return Response.ok(new CountResponse(count)).build();
        } catch (Exception e) {
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity(new ErrorResponse("Erreur lors du comptage des vies: " + e.getMessage()))
                    .build();
        }
    }

    // Classes pour les réponses JSON
    
    public static class ErrorResponse {
        private String error;

        public ErrorResponse() {}
        
        public ErrorResponse(String error) {
            this.error = error;
        }

        public String getError() {
            return error;
        }

        public void setError(String error) {
            this.error = error;
        }
    }

    public static class SuccessResponse {
        private String message;

        public SuccessResponse() {}
        
        public SuccessResponse(String message) {
            this.message = message;
        }

        public String getMessage() {
            return message;
        }

        public void setMessage(String message) {
            this.message = message;
        }
    }

    public static class CountResponse {
        private long count;

        public CountResponse() {}
        
        public CountResponse(long count) {
            this.count = count;
        }

        public long getCount() {
            return count;
        }

        public void setCount(long count) {
            this.count = count;
        }
    }
}
