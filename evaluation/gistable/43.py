import astropy.units as u
from astropy.coordinates import ICRSCoordinates
from streams.coordinates import SgrCoordinates, OrphanCoordinates

icrs = ICRSCoordinates(15.34167, 1.53412, unit=(u.hour, u.degree))
sgr = icrs.transform_to(SgrCoordinates)
print(sgr.Lambda, sgr.Beta)

orp = sgr.transform_to(OrphanCoordinates)
print(orp.Lambda, orp.Beta)