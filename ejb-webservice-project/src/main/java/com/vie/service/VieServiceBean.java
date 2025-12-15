package com.vie.service;

import com.vie.entity.Vie;
import jakarta.ejb.Stateless;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.TypedQuery;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

@Stateless
public class VieServiceBean implements VieServiceRemote {

    private static final Logger LOGGER = Logger.getLogger(VieServiceBean.class.getName());

    @PersistenceContext(unitName = "viePU")
    private EntityManager entityManager;

    @Override
    public Vie create(Vie vie) {
        try {
            LOGGER.log(Level.INFO, "Creating new Vie: {0}", vie);
            entityManager.persist(vie);
            entityManager.flush();
            LOGGER.log(Level.INFO, "Vie created successfully with ID: {0}", vie.getLid());
            return vie;
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Error creating Vie", e);
            throw new RuntimeException("Error creating Vie: " + e.getMessage(), e);
        }
    }

    @Override
    public Vie findById(Long id) {
        try {
            LOGGER.log(Level.INFO, "Finding Vie with ID: {0}", id);
            Vie vie = entityManager.find(Vie.class, id);
            if (vie == null) {
                LOGGER.log(Level.WARNING, "Vie not found with ID: {0}", id);
            }
            return vie;
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Error finding Vie", e);
            throw new RuntimeException("Error finding Vie: " + e.getMessage(), e);
        }
    }

    @Override
    public List<Vie> findAll() {
        try {
            LOGGER.log(Level.INFO, "Fetching all Vies");
            TypedQuery<Vie> query = entityManager.createNamedQuery("Vie.findAll", Vie.class);
            List<Vie> vies = query.getResultList();
            LOGGER.log(Level.INFO, "Found {0} Vies", vies.size());
            return vies;
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Error fetching all Vies", e);
            throw new RuntimeException("Error fetching all Vies: " + e.getMessage(), e);
        }
    }

    @Override
    public Vie update(Vie vie) {
        try {
            LOGGER.log(Level.INFO, "Updating Vie with ID: {0}", vie.getLid());
            
            // Vérifier si l'entité existe
            Vie existingVie = entityManager.find(Vie.class, vie.getLid());
            if (existingVie == null) {
                LOGGER.log(Level.WARNING, "Vie not found for update with ID: {0}", vie.getLid());
                throw new RuntimeException("Vie not found with ID: " + vie.getLid());
            }
            
            // Mettre à jour les champs
            existingVie.setLibelle(vie.getLibelle());
            existingVie.setNombreVieInitiale(vie.getNombreVieInitiale());
            
            Vie updatedVie = entityManager.merge(existingVie);
            entityManager.flush();
            LOGGER.log(Level.INFO, "Vie updated successfully");
            return updatedVie;
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Error updating Vie", e);
            throw new RuntimeException("Error updating Vie: " + e.getMessage(), e);
        }
    }

    @Override
    public boolean delete(Long id) {
        try {
            LOGGER.log(Level.INFO, "Deleting Vie with ID: {0}", id);
            Vie vie = entityManager.find(Vie.class, id);
            
            if (vie == null) {
                LOGGER.log(Level.WARNING, "Vie not found for deletion with ID: {0}", id);
                return false;
            }
            
            entityManager.remove(vie);
            entityManager.flush();
            LOGGER.log(Level.INFO, "Vie deleted successfully");
            return true;
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Error deleting Vie", e);
            throw new RuntimeException("Error deleting Vie: " + e.getMessage(), e);
        }
    }

    @Override
    public long count() {
        try {
            LOGGER.log(Level.INFO, "Counting all Vies");
            TypedQuery<Long> query = entityManager.createQuery(
                "SELECT COUNT(v) FROM Vie v", Long.class);
            Long count = query.getSingleResult();
            LOGGER.log(Level.INFO, "Total Vies: {0}", count);
            return count;
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Error counting Vies", e);
            throw new RuntimeException("Error counting Vies: " + e.getMessage(), e);
        }
    }
}
