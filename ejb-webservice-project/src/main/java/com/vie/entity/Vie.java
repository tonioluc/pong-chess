package com.vie.entity;

import jakarta.persistence.*;
import java.io.Serializable;

@Entity
@Table(name = "Vie")
@NamedQueries({
    @NamedQuery(name = "Vie.findAll", query = "SELECT v FROM Vie v"),
    @NamedQuery(name = "Vie.findById", query = "SELECT v FROM Vie v WHERE v.lid = :lid")
})
public class Vie implements Serializable {

    private static final long serialVersionUID = 1L;

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "lid")
    private Long lid;

    @Column(name = "libelle", nullable = false, length = 100)
    private String libelle;

    @Column(name = "nombreVieInitiale")
    private Integer nombreVieInitiale;

    // Constructeurs
    public Vie() {
    }

    public Vie(String libelle, Integer nombreVieInitiale) {
        this.libelle = libelle;
        this.nombreVieInitiale = nombreVieInitiale;
    }

    // Getters et Setters
    public Long getLid() {
        return lid;
    }

    public void setLid(Long lid) {
        this.lid = lid;
    }

    public String getLibelle() {
        return libelle;
    }

    public void setLibelle(String libelle) {
        this.libelle = libelle;
    }

    public Integer getNombreVieInitiale() {
        return nombreVieInitiale;
    }

    public void setNombreVieInitiale(Integer nombreVieInitiale) {
        this.nombreVieInitiale = nombreVieInitiale;
    }

    // toString, equals, hashCode
    @Override
    public String toString() {
        return "Vie{" +
                "lid=" + lid +
                ", libelle='" + libelle + '\'' +
                ", nombreVieInitiale=" + nombreVieInitiale +
                '}';
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Vie vie = (Vie) o;
        return lid != null && lid.equals(vie.lid);
    }

    @Override
    public int hashCode() {
        return getClass().hashCode();
    }
}
