package com.vie.service;

import com.vie.entity.Vie;
import jakarta.ejb.Remote;
import java.util.List;

@Remote
public interface VieServiceRemote {
    
    /**
     * Créer une nouvelle Vie
     * @param vie L'entité Vie à créer
     * @return La Vie créée avec son ID
     */
    Vie create(Vie vie);
    
    /**
     * Récupérer une Vie par son ID
     * @param id L'identifiant de la Vie
     * @return La Vie trouvée ou null
     */
    Vie findById(Long id);
    
    /**
     * Récupérer toutes les Vies
     * @return Liste de toutes les Vies
     */
    List<Vie> findAll();
    
    /**
     * Mettre à jour une Vie existante
     * @param vie L'entité Vie à mettre à jour
     * @return La Vie mise à jour
     */
    Vie update(Vie vie);
    
    /**
     * Supprimer une Vie par son ID
     * @param id L'identifiant de la Vie à supprimer
     * @return true si la suppression a réussi, false sinon
     */
    boolean delete(Long id);
    
    /**
     * Compter le nombre total de Vies
     * @return Le nombre de Vies
     */
    long count();
}
