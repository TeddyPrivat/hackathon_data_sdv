sns.set_theme(style="darkgrid")
fig, axes = plt.subplots(3, 2, figsize=(18, 11),
                          gridspec_kw={'width_ratios': [3, 1]})

configs = [
    ('CO2_ppm', 'CO₂', '#16a34a', 'ppm', [
        "🌿 Avant 1800 : ~280 ppm",
        "⚠️  1988 : franchit 350 ppm",
        "🚨 2016 : franchit 400 ppm",
        "📍 2024 : 423 ppm (record)",
        "",
        "Causes principales :",
        "• Combustibles fossiles",
        "• Déforestation",
        "• Ciment & industrie",
    ]),
    ('CH4_ppb', 'CH₄ Méthane', '#ea580c', 'ppb', [
        "🌿 Avant 1800 : ~722 ppb",
        "📍 2024 : ~1930 ppb",
        "📈 Hausse : +167% depuis",
        "   l'ère préindustrielle",
        "",
        "Causes principales :",
        "• Élevage bovin",
        "• Rizières",
        "• Fuites gaz naturel",
        "• Décharges",
    ]),
    ('N2O_ppb', 'N₂O Protoxyde d\'azote', '#7c3aed', 'ppb', [
        "🌿 Avant 1800 : ~270 ppb",
        "📍 2024 : ~338 ppb",
        "⚡ Pouvoir réchauffant :",
        "   298x supérieur au CO₂",
        "",
        "Causes principales :",
        "• Engrais azotés",
        "• Élevage",
        "• Industrie chimique",
        "• Combustion biomasse",
    ]),
]

for i, (col, label, couleur, unite, contexte) in enumerate(configs):
    ax_graph = axes[i][0]
    ax_text  = axes[i][1]

    # ── Graphique ──
    donnees = df_large.dropna(subset=[col])
    ax_graph.plot(donnees['DATE'], donnees[col],
                  color=couleur, linewidth=1, alpha=0.35)
    
    ann = donnees.copy()
    ann['year'] = ann['DATE'].dt.year
    ann_moy = ann.groupby('year')[col].mean().reset_index()
    ax_graph.plot(
        pd.to_datetime(ann_moy['year'].astype(str)),
        ann_moy[col],
        color=couleur, linewidth=2.5
    )

    # Seuils CO2
    if col == 'CO2_ppm':
        ax_graph.axhline(350, color='orange', linestyle=':', linewidth=1.5, alpha=0.8)
        ax_graph.axhline(400, color='red',    linestyle=':', linewidth=1.5, alpha=0.8)
        ax_graph.text(donnees['DATE'].iloc[2], 352, '350 ppm', fontsize=7.5, color='orange')
        ax_graph.text(donnees['DATE'].iloc[2], 402, '400 ppm', fontsize=7.5, color='red')

    # Annotation dernière valeur
    derniere = donnees[col].dropna().iloc[-1]
    ax_graph.annotate(
        f'{derniere:.1f} {unite}',
        xy=(donnees['DATE'].iloc[-1], derniere),
        xytext=(-70, -18), textcoords='offset points',
        fontsize=9, color=couleur, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color=couleur, lw=1.2)
    )

    ax_graph.set_ylabel(f'{label} ({unite})', fontsize=10)
    if i == 2:
        ax_graph.set_xlabel('Année', fontsize=10)

    # ── Panneau texte ──
    ax_text.axis('off')
    ax_text.set_facecolor('#f8f4ff')

    # Cadre coloré
    rect = plt.Rectangle((0, 0), 1, 1,
                           transform=ax_text.transAxes,
                           facecolor='#f8f4ff',
                           edgecolor=couleur, linewidth=2)
    ax_text.add_patch(rect)

    # Titre du panneau
    ax_text.text(0.5, 0.97, label,
                 transform=ax_text.transAxes,
                 fontsize=10, fontweight='bold', color=couleur,
                 ha='center', va='top')

# Ligne séparatrice
    ax_text.axhline(y=0.91, xmin=0.05, xmax=0.95,
                    color=couleur, linewidth=0.8, alpha=0.5)

    # Texte de contexte
    y_pos = 0.86
    for ligne in contexte:
        style = 'bold' if ligne.startswith('Causes') else 'normal'
        size  = 8.5 if ligne.startswith('•') or ligne == '' else 9
        ax_text.text(0.07, y_pos, ligne,
                     transform=ax_text.transAxes,
                     fontsize=size, fontstyle='normal',
                     fontweight=style,
                     color='#1e1e2e', va='top')
        y_pos -= 0.09

# ── Titre global ──
fig.suptitle(
    '🌍 Évolution des Gaz à Effet de Serre — Source : NOAA Global Monitoring Laboratory',
    fontsize=13, fontweight='bold', y=1.01
)

plt.tight_layout()
plt.savefig('data/ges_3gaz_contexte.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ Sauvegardé → data/ges_3gaz_contexte.png")