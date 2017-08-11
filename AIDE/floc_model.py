# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 16:50:46 2017

@author: Sage Weber-Shirk

Last revised: Tue Aug 8 2017
By: Sage Weber-Shirk

This file contains flocculation functions pertaining to the design of
physical/chemical unit processes for AguaClara water treatment plants
"""

######################### Imports #########################
import numpy as np

try:
    from AguaClara_design.units import unit_registry as u
    from AguaClara_design import physchem as pc
except ModuleNotFoundError:
    from AIDE.units import unit_registry as u
    from AIDE import physchem as pc

u.enable_contexts('chem')

##################### Class Definition #####################


class Chemical:
    def __init__(self, name, diameter, density, molecWeight, Precipitate,
                 AluminumMPM=None):
        self.name = name
        self.Diameter = diameter
        self.Density = density
        self.MolecWeight = molecWeight
        self.AluminumMPM = AluminumMPM
        self.Precip = Precipitate
        if self.Precip == self.name:
            self.PrecipName = name
            self.PrecipDiameter = diameter
            self.PrecipDensity = density
            self.PrecipMolecWeight = molecWeight
            self.PrecipAluminumMPM = AluminumMPM
        else:
            self.PrecipName = Precipitate

    def define_Precip(self, diameter, density, molecweight, alumMPM):
        self.PrecipDiameter = diameter
        self.PrecipDensity = density
        self.PrecipMolecWeight = molecweight
        self.PrecipAluminumMPM = alumMPM


################## Chemical Definitions ##################
# name, diameter in m, density in kg/m³, molecular weight in kg/mole
PACl = Chemical('PACl', (90 * u.nm).to(u.m).magnitude, 1138, 1.039,
                'PACl', AluminumMPM=13)

Alum = Chemical('Alum', (70 * u.nm).to(u.m).magnitude, 2420, 0.59921,
                'AlOH3', AluminumMPM=2)
Alum.define_Precip((70 * u.nm).to(u.m).magnitude, 2420, 0.078, 1)

HumicAcid = Chemical('Humic Acid', 72 * 10**-9, 1780, None, 'Humic Acid')

################### Necessary Constants ###################
# Fractal diameter, based on data from Adachi.
DIAM_FRACTAL = 2.3
# Diameter of the clay particles in meters.
DIAM_CLAY = 7 * 10**-6
# Ratio of clay platelet height to diameter.
RATIO_HEIGHT_DIAM = 0.1
# Density of clay in kg/m**3.
DENS_CLAY = 2650
# Ration between inner viscous length scale and Kolmogorov length scale.
RATIO_KOLMOGOROV = 50
# Shape factor for drag on flocs used in terminal velocity equation.
PHI_FLOC = 45/24
# The Avogadro constant.
NUM_AVOGADRO = 6.0221415 * 10**23
# Molecular weight of aluminum in kg/mole.
MOLEC_WEIGHT_ALUMINUM = 0.027


######################## Functions ########################
@u.wraps(u.kg/u.m**3, None, False)
def dens_alum_nanocluster(coag):
    """Return the density of the aluminum in the nanocluster.

    This is useful for determining the volume of nanoclusters
    given a concentration of aluminum.
    """
    density = (coag.PrecipDensity * MOLEC_WEIGHT_ALUMINUM
               * coag.PrecipAluminumMPM / coag.PrecipMolecWeight)
    return density


@u.wraps(u.kg/u.m**3, [u.kg/u.m**3, u.degK], False)
def dens_pacl_solution(ConcAluminum, temp):
    """Return the density of the PACl solution.

    From Stock Tank Mixing report Fall 2013:
    https://confluence.cornell.edu/download/attachments/137953883/20131213_Research_Report.pdf
    """
    return ((0.492 * ConcAluminum * PACl.MolecWeight
             / (PACl.AluminumMPM * MOLEC_WEIGHT_ALUMINUM)
             ) + pc.density_water(temp).magnitude
            )


@u.wraps(u.kg/u.m**3, [u.kg/u.m**3, None], False)
def conc_precipitate(ConcAluminum, coag):
    """Return coagulant precipitate concentration given aluminum dose.

    Note that conc_precipitate returns a value that varies from the equivalent
    MathCAD function beginning at the third decimal place. The majority of
    functions below this point in the file ultimately call on conc_precipitate
    at some point, and will not return the same value as their equivalent
    function in MathCAD. This is known.
    """
    return ((ConcAluminum / MOLEC_WEIGHT_ALUMINUM)
            * (coag.PrecipMolecWeight / coag.PrecipAluminumMPM)
            )


@u.wraps(u.kg/u.m**3, [u.kg/u.m**3, u.kg/u.m**3, None], False)
def conc_floc(ConcAluminum, concClay, coag):
    """Return floc density given aluminum dose, turbidity, and coagulant"""
    return conc_precipitate(ConcAluminum, coag).magnitude + concClay


@u.wraps(u.mol/u.m**3, u.kg/u.m**3, False)
def moles_aluminum(ConcAluminum):
    """Return the # of moles aluminum given aluminum concentration."""
    return (ConcAluminum / MOLEC_WEIGHT_ALUMINUM)


@u.wraps(u.m, u.kg/u.m**3, False)
def sep_dist_aluminum(ConcAluminum):
    """Return the separation distance between aluminum molecules."""
    return (1 / (NUM_AVOGADRO * moles_aluminum(ConcAluminum).magnitude))**(1/3)


@u.wraps(1/u.m**3, [u.kg/u.m**3, u.m], False)
def num_clay(ConcClay, DiamClay):
    return ConcClay / ((DENS_CLAY * np.pi * DiamClay**3) / 6)


@u.wraps(u.m, [u.kg/u.m**3, u.m], False)
def sep_dist_clay(ConcClay, DiamClay):
    """Return the separation distance between clay particles."""
    return ((DENS_CLAY / ConcClay) * ((np.pi * DiamClay**3) / 6))**(1/3)


@u.wraps(1/u.m**3, [u.kg/u.m**3, None], False)
def num_nanoclusters(ConcAluminum, coag):
    return (ConcAluminum / (dens_alum_nanocluster(coag).magnitude
                            * np.pi * coag.Diameter**3
                            ))


@u.wraps(None, [u.kg/u.m**3, u.kg/u.m**3, None], False)
def frac_vol_floc_initial(ConcAluminum, ConcClay, coag):
    return ((conc_precipitate(ConcAluminum, coag).magnitude/coag.PrecipDensity)
            + (ConcClay / DENS_CLAY))


####################### p functions #######################
def p(C, Cprime):
    return -np.log10(C/Cprime)


def invp(pC, Cprime):
    return Cprime * 10**-pC


#################### Fractal functions ####################
@u.wraps(u.m, [u.dimensionless, u.m, u.dimensionless], False)
def diam_fractal(DiamFractal, DiamInitial, NumCol):
    """Return the diameter of a floc given NumCol doubling collisions."""
    return DiamInitial * 2**(NumCol / DiamFractal)


@u.wraps(None, [u.dimensionless, u.m, u.m], False)
def num_coll_reqd(DiamFractal, DiamInit, DiamTarget):
    """Return the number of doubling collisions required.

    Calculates the number of doubling collisions required to produce
    a floc of diameter DiamTarget.
    """
    return DiamFractal * np.log2(DiamTarget/DiamInit)


@u.wraps(u.m, [u.kg/u.m**3, u.kg/u.m**3, None,
               u.dimensionless, u.m, u.m], False)
def sep_dist_floc(ConcAluminum, ConcClay, coag,
                  DiamFractal, DiamInit, DiamTarget):
    """Return separation distance as a function of floc size."""
    return (DiamInit
            * (np.pi/(6
                      * frac_vol_floc_initial(ConcAluminum, ConcClay, coag)
                      ))**(1/3)
            * (DiamTarget / DiamInit)**(DiamFractal / 3)
            )


@u.wraps(u.m, [u.kg/u.m**3, u.kg/u.m**3, None, u.dimensionless,
               u.m, u.m], False)
def frac_vol_floc(ConcAluminum, ConcClay, coag, DiamFractal,
                  DiamInit, DiamTarget):
    """Return the floc volume fraction."""
    return (frac_vol_floc_initial(ConcAluminum, ConcClay, coag)
            * (DiamTarget / DiamInit)**(3-DiamFractal)
            )


@u.wraps(u.kg/u.m**3, [u.kg/u.m**3, u.kg/u.m**3, None], False)
def dens_floc_init(ConcAluminum, ConcClay, coag):
    """Return the density of the initial floc.

    Initial floc is made primarily of the primary colloid and nanoglobs.
    """
    return (conc_floc(ConcAluminum, ConcClay, coag).magnitude
            / frac_vol_floc_initial(ConcAluminum, ConcClay, coag)
            )


#################### Flocculation Model ####################
@u.wraps(None, u.m, False)
def ratio_clay_sphere(RatioHeightDiameter):
    """Return the surface area to volume ratio for clay.

    Normalized by surface area to volume ratio for a sphere.
    """
    return (1/2 + RatioHeightDiameter) * (2 / (3*RatioHeightDiameter))**(2/3)


@u.wraps(None, [u.kg/u.m**3, u.m, u.m, u.kg/u.m**3, u.dimensionless], False)
def ratio_area_clay_total(ConcClay, DiamClay, DiamTube,
                          DensityClay, RatioHeightDiameter):
    """Return the surface area of clay normalized by total surface area.

    Total surface area is a combination of clay and reactor wall
    surface areas. This function is used to estimate how much coagulant
    actually goes to the clay.
    """
    return (1
            / (1
               + (2 * DiamClay
                  / (3 * DiamTube * ratio_clay_sphere(RatioHeightDiameter)
                     * (ConcClay / DensityClay)
                     )
                  )
               )
            )


@u.wraps(None, [u.kg/u.m**3, u.kg/u.m**3, None,
                u.m, u.m, u.kg/u.m**3, u.dimensionless], False)
def gamma_coag(ConcClay, ConcAluminum, coag,
               DiamTube, DiamClay, DensityClay, RatioHeightDiameter):
    """Return the coverage of clay with nanoglobs.

    This function accounts for loss to the tube flocculator walls
    and a poisson distribution on the clay given random hits by the
    nanoglobs. The poisson distribution results in the coverage only
    gradually approaching full coverage as coagulant dose increases.
    """
    return (1 - np.exp(
                       ((- frac_vol_floc_initial(ConcAluminum, 0, coag)
                         * DiamClay
                         )
                        / (frac_vol_floc_initial(0, ConcClay, coag)
                           * coag.Diameter
                           )
                        )
                       * (1 / np.pi)
                       * (ratio_area_clay_total(ConcClay, DiamClay,
                                                DiamTube, DensityClay,
                                                RatioHeightDiameter)
                          / ratio_clay_sphere(RatioHeightDiameter)
                          )
                       )
            )


@u.wraps(None, [u.kg/u.m**3, u.kg/u.m**3, None, None], False)
def gamma_humic_acid_to_coag(ConcAl, ConcNatOrgMat, NatOrgMat, coag):
    return min(((ConcNatOrgMat / conc_precipitate(ConcAl, coag).magnitude)
                * (coag.Density / NatOrgMat.Density)
                * (coag.Diameter / (4 * NatOrgMat.Diameter))
                ),
               1)


@u.wraps(None, [u.m, u.m, u.kg/u.m**3, u.kg/u.m**3, u.kg/u.m**3,
                u.kg/u.m**3, None, None, u.dimensionless], False)
def _pacl_term(DiamTube, DiamClay, DensityClay, ConcClay, ConcAl,
               ConcNatOrgMat, NatOrgMat, coag, RatioHeightDiameter):
    return (gamma_coag(ConcClay, ConcAl, coag, DiamTube, DiamClay,
                       DensityClay, RatioHeightDiameter)
            * (1 - gamma_humic_acid_to_coag(ConcAl, ConcNatOrgMat,
                                            NatOrgMat, coag))
            )


@u.wraps(None, [u.m, u.m, u.kg/u.m**3, u.kg/u.m**3, u.kg/u.m**3,
                u.kg/u.m**3, None, None, u.dimensionless], False)
def alpha_pacl_clay(DiamTube, DiamClay, DensityClay, ConcClay, ConcAl,
                    ConcNatOrgMat, NatOrgMat, coag, RatioHeightDiameter):
    PAClTerm = _pacl_term(DiamTube, DiamClay, DensityClay, ConcClay, ConcAl,
                          ConcNatOrgMat, NatOrgMat, coag, RatioHeightDiameter)
    return 2 * (PAClTerm * (1 - gamma_coag(ConcClay, ConcAl, coag, DiamTube,
                                           DiamClay, DensityClay,
                                           RatioHeightDiameter)))


@u.wraps(None, [u.m, u.m, u.kg/u.m**3, u.kg/u.m**3, u.kg/u.m**3,
                u.kg/u.m**3, None, None, u.dimensionless], False)
def alpha_pacl_pacl(DiamTube, DiamClay, DensityClay, ConcClay, ConcAl,
                    ConcNatOrgMat, NatOrgMat, coag, RatioHeightDiameter):
    PAClTerm = _pacl_term(DiamTube, DiamClay, DensityClay, ConcClay, ConcAl,
                          ConcNatOrgMat, NatOrgMat, coag, RatioHeightDiameter)
    return PAClTerm ** 2


@u.wraps(None, [u.m, u.m, u.kg/u.m**3, u.kg/u.m**3, u.kg/u.m**3,
                u.kg/u.m**3, None, None, u.dimensionless], False)
def alpha_pacl_nat_org_mat(DiamTube, DiamClay, DensityClay, ConcClay, ConcAl,
                           ConcNatOrgMat, NatOrgMat, coag, 
                           RatioHeightDiameter):
    PAClTerm = _pacl_term(DiamTube, DiamClay, DensityClay, ConcClay, ConcAl,
                          ConcNatOrgMat, NatOrgMat, coag, RatioHeightDiameter)
    return (2 * PAClTerm
            * gamma_coag(ConcClay, ConcAl, coag, DiamTube, DiamClay,
                         DensityClay, RatioHeightDiameter)
            * gamma_humic_acid_to_coag(ConcAl, ConcNatOrgMat, NatOrgMat, coag))


@u.wraps(None, [u.m, u.m, u.kg/u.m**3, u.kg/u.m**3, u.kg/u.m**3, u.kg/u.m**3, 
                None, None, u.dimensionless], False)
def alpha(DiamTube, DiamClay, DensityClay, ConcClay, ConcAl, ConcNatOrgMat, 
          NatOrgMat, coag, RatioHeightDiameter):
    return (alpha_pacl_nat_org_mat(DiamTube, DiamClay, DensityClay, ConcClay, 
                                   ConcAl, ConcNatOrgMat, NatOrgMat, coag, 
                                   RatioHeightDiameter)
            + alpha_pacl_pacl(DiamTube, DiamClay, DensityClay, ConcClay, 
                              ConcAl, ConcNatOrgMat, NatOrgMat, coag, 
                              RatioHeightDiameter)
            + alpha_pacl_clay(DiamTube, DiamClay, DensityClay, ConcClay, 
                              ConcAl, ConcNatOrgMat, NatOrgMat, coag, 
                              RatioHeightDiameter)
            )


@u.wraps(None, [u.W/u.kg, u.degK, u.s, u.m, u.m, u.m,
                u.kg/u.m**3, u.kg/u.m**3, u.kg/u.m**3, u.kg/u.m**3, None,
                None, u.dimensionless, u.dimensionless], False)
def pc_viscous(EnergyDis, Temp, Time, DiamInit, DiamTube, DiamClay,
               DensityClay, ConcClay, ConcAl, ConcNatOrgMat, NatOrgMat,
               coag, FittingParam, RatioHeightDiameter):
    return ((3/2)
            * np.log10((2/3) * np.pi * FittingParam * Time
                       * np.sqrt(EnergyDis
                                 / (pc.viscosity_kinematic(Temp).magnitude)
                                 )
                       * alpha(DiamTube, DiamClay, DensityClay, ConcClay,
                               ConcAl, ConcNatOrgMat, NatOrgMat, coag,
                               RatioHeightDiameter)
                       * (DiamInit
                          / sep_dist_clay(ConcClay, DiamInit).magnitude
                          ) ** 2
                       + 1
                       )
            )


@u.wraps(u.kg/u.m**3, [u.kg/u.m**3, u.kg/u.m**3, u.dimensionless, u.m, u.m,
                       None, u.degK], False)
def dens_floc(ConcAl, ConcClay, DiamFractal, DiamInit, DiamTarget, coag, Temp):
    """Calculate floc density as a function of size."""
    WaterDensity = pc.density_water(Temp).magnitude
    return ((dens_floc_init(ConcAl, ConcClay, coag).magnitude - WaterDensity)
            * (DiamInit / DiamTarget)**(3 - DiamFractal)
            + WaterDensity
            )


@u.wraps(u.m/u.s, [u.kg/u.m**3, u.kg/u.m**3, None, u.dimensionless,
                   u.m, u.m, u.degK], False)
def vel_term_floc(ConcAl, ConcClay, coag, DiamFractal,
                  DiamInit, DiamTarget, Temp):
    """Calculate floc terminal velocity."""
    WaterDensity = pc.density_water(Temp).magnitude
    return (((pc.gravity.magnitude * DiamInit**2)
             / (18 * PHI_FLOC * pc.viscosity_kinematic(Temp).magnitude)
             )
            * ((dens_floc_init(ConcAl, ConcClay, coag).magnitude
                - WaterDensity
                )
               / WaterDensity
               )
            * (DiamTarget / DiamInit) ** (DiamFractal - 1)
            )


@u.wraps(u.m, [u.kg/u.m**3, u.kg/u.m**3, None, u.dimensionless,
               u.m, u.m/u.s, u.degK], False)
def diam_floc_vel_term(ConcAl, ConcClay, coag, DiamFractal,
                       DiamInit, VelTerm, Temp):
    """Calculate floc diamter as a function of terminal velocity."""
    WaterDensity = pc.density_water(Temp).magnitude
    return (DiamInit * (((18 * VelTerm * PHI_FLOC
                          * pc.viscosity_kinematic(Temp).magnitude
                          )
                         / (pc.gravity.magnitude * DiamInit**2)
                         )
                         * (WaterDensity
                            / (dens_floc_init(ConcAl, ConcClay, coag).magnitude
                               - WaterDensity
                               )
                            )
                        ) ** (1 / (DiamFractal - 1))
            )


@u.wraps(u.s, [u.kg/u.m**3, u.kg/u.m**3, None, u.dimensionless, u.m,
               u.m, u.W/u.kg,  u.degK, u.m, u.dimensionless, u.kg/u.m**3],
         False)
def time_col_laminar(ConcAl, ConcClay, coag, DiamFractal, DiamInit,
                     DiamTarget, EnergyDis, Temp, DiamTube,
                     RatioHeightDiameter, DensityClay):
    """Calculate single collision time for laminar flow mediated collisions.

    Calculated as a function of floc size.
    """
    return (((1/6) * ((6/np.pi)**(1/3))
             * frac_vol_floc_initial(ConcAl, ConcClay, coag)**(-2/3)
             * (pc.viscosity_kinematic(Temp).magnitude / EnergyDis)**(1/2)
             * (DiamTarget / DiamInit)**(2*DiamFractal/3 - 2)
             )  # End of the numerator
            / (gamma_coag(ConcClay, ConcAl, coag, DiamTube,
                          DiamInit, DensityClay, RatioHeightDiameter)
               )  # End of the denominator
            )


@u.wraps(u.s, [u.kg/u.m**3, u.kg/u.m**3, None, u.dimensionless, u.m,
               u.m, u.W/u.kg], False)
def time_col_turbulent(ConcAl, ConcClay, coag, DiamFractal, DiamInit,
                       DiamTarget, EnergyDis):
    """Calculate single collision time for turbulent flow mediated collisions.

    Calculated as a function of floc size.
    """
    return((1/6) * (6/np.pi)**(1/9) * EnergyDis**(-1/3) * DiamTarget**(2/3)
           * frac_vol_floc_initial(ConcAl, ConcClay, coag)**(-8/9)
           * (DiamTarget / DiamInit)**((8*(DiamFractal-3)) / 9)
           )


########### Kolmogorov and viscous length scales ###########
@u.wraps(u.m, [u.W/u.kg, u.degK], False)
def eta_kolmogorov(EnergyDis, Temp):
    return ((pc.viscosity_kinematic(Temp).magnitude**3) / EnergyDis) ** (1/4)


@u.wraps(u.m, [u.W/u.kg, u.degK], False)
def lambda_vel(EnergyDis, Temp):
    return RATIO_KOLMOGOROV * eta_kolmogorov(EnergyDis, Temp).magnitude


@u.wraps(u.m, [u.kg/u.m**3, u.kg/u.m**3, None, u.m, u.dimensionless,
               u.W/u.kg, u.degK], False)
def diam_kolmogorov(ConcAl, ConcClay, coag, DiamInit,
                    DiamFractal, EnergyDis, Temp):
    """Return the size of the floc with separation distances equal to
    the Kolmogorov length and the inner viscous length scale.
    """
    return (DiamInit
            * ((eta_kolmogorov(EnergyDis, Temp).magnitude / DiamInit)
               * ((6 * frac_vol_floc_initial(ConcAl, ConcClay, coag))
                  / np.pi
                  )**(1/3)
               )**(3 / DiamFractal)
            )


@u.wraps(u.m, [u.kg/u.m**3, u.kg/u.m**3, None, u.m, u.dimensionless,
               u.W/u.kg, u.degK], False)
def diam_vel(ConcAl, ConcClay, coag, DiamInit, DiamFractal, EnergyDis, Temp):
    return (DiamInit
            * ((lambda_vel(EnergyDis, Temp).magnitude / DiamInit)
               * ((6 * frac_vol_floc_initial(ConcAl,ConcClay,coag))
                  / np.pi
                  )**(1/3)
               )**(3/DiamFractal)
            )


@u.wraps(u.m, u.W/u.kg, False)
def diam_floc_max(epsMax):
    """Return floc size as a function of energy dissipation rate.

    Based on Ian Tse's work with floc size as a function of energy
    dissipation rate. This is for the average energy dissipation rate
    in a tube flocculator. It isn't clear how to convert this to the
    turbulent flow case. Maybe the flocs are mostly experiencing viscous
    shear. But that isn't clear. Some authors have made the case that
    floc breakup is due to viscous effects. If that is the case, then
    the results from the tube flocculator should be applicable to the
    turbulent case. We will have to account for the temporal and spatial
    variability in the turbulent energy dissipation rate. The factor of
    95 μm is based on the assumption that the ratio of the max to
    average energy dissipation rate for laminar flow is approximately 2.
    """
    return 9.5 * 10**-5 * (1 / (epsMax)**(1/3))


@u.wraps(u.W/u.kg, u.m, False)
def ener_dis_diam_floc(Diam):
    """Return max energy dissipation rate as a function of max floc diameter.

    This equation is under suspicion.
    """
    return (9.5 * 10**-5 / Diam) ** 3


##### Velocity gradient in tubing for lab scale laminar flow flocculators #####
@u.wraps(1/u.s, [u.m**3/u.s, u.m], False)
def g_straight(PlantFlow, IDTube):
    return 64 * PlantFlow / (3 * np.pi * IDTube**3)


@u.wraps(None, [u.m**3/u.s, u.m, u.degK], False)
def reynolds_rapid_mix(PlantFlow, IDTube, Temp):
    return (4 * PlantFlow / (np.pi * IDTube
                             * pc.viscosity_kinematic(Temp).magnitude))


@u.wraps(None, [u.m**3/u.s, u.m, u.m, u.degK], False)
def dean_number(PlantFlow, IDTube, RadiusCoil, Temp):
    """Return the Dean Number.

    The Dean Number is a dimensionless parameter that is the unfortunate
    combination of Reynolds and tube curvature. It would have been better
    to keep the Reynolds number and define a simple dimensionless geometric
    parameter.
    """
    return (reynolds_rapid_mix(PlantFlow, IDTube, Temp)
            * (IDTube / (2 * RadiusCoil))**(1/2)
            )


@u.wraps(1/u.s, [u.m**3/u.s, u.m, u.m, u.degK], False)
def g_coil(FlowPlant, IDTube, RadiusCoil, Temp):
    """We need a reference for this.

    Karen's thesis likely has this equation and the reference.
    """
    return (g_straight(FlowPlant, IDTube).magnitude
            * (1
               + 0.033 * np.log10(dean_number(FlowPlant,IDTube,RadiusCoil,Temp)
                                  ) ** 4
               ) ** (1/2)
            )


@u.wraps(u.s, [u.m, u.m, u.m**3/u.s], False)
def time_res_tube(IDTube, LengthTube, FlowPlant):
    """Calculate residence time in the flocculator."""
    return LengthTube * np.pi * (IDTube**2 / 4) / FlowPlant


@u.wraps(None, [u.m**3/u.s, u.m, u.m, u.m, u.degK], False)
def g_time_res(FlowPlant, IDTube, RadiusCoil, LengthTube, Temp):
    """G Residence Time calculated for a coiled tube flocculator."""
    return (g_coil(FlowPlant, IDTube, RadiusCoil, Temp).magnitude
            * time_res_tube(IDTube, LengthTube, FlowPlant).magnitude
            )