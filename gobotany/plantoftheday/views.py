from datetime import date, datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse

from gobotany.core import botany
from gobotany.core.models import Taxon
from gobotany.core.partner import which_partner, render_per_partner
from gobotany.plantoftheday.models import PlantOfTheDay


def _get_plants_of_the_day(max_number_plants, partner_name):
    """Get recent plants of the day, generating some if needed."""

    # Generate today's Plant of the Day if it hasn't been already.
    # If there is a gap of any recent days where no Plant of the Day
    # record exists yet, generate records for those days too.
    for i in range(max_number_plants):
        day = date.today() - timedelta(days=i)
        plant_of_the_day = PlantOfTheDay.objects.filter(
            last_seen=day, partner_short_name=partner_name, include=True)
        if len(plant_of_the_day) == 0:
            # No Plant of the Day exists for that day, so generate one.
            plant_of_the_day = PlantOfTheDay.get_by_date.for_day(
                day, partner_name)

    # Now that any new records that were needed have been generated,
    # build the list of plants to pass to the template.
    plants = []
    plant_records = (PlantOfTheDay.objects.filter(
        include=True,
        last_seen__isnull=False,
        partner_short_name=partner_name)
        .order_by('-last_seen'))[:max_number_plants]

    for plant_record in plant_records:
        plant = {}
        plant['scientific_name'] = plant_record.scientific_name

        # Use the last_updated field because it is a date/time field,
        # rather than last_seen which is just a date field, because the
        # time is needed for stamping each post. However, the actual
        # query above must use last_seen to get the correct plant records.
        post_datetime = datetime.combine(plant_record.last_seen,
                                         plant_record.last_updated.time())
        date_time = post_datetime.isoformat()
        # Use a set time for each post in order to help keep posts
        # happening consistently once per calendar day, rather than
        # random times which can end up crossing days with time zones.
        date_time = date_time.split('T')[0] + 'T05:02:00'
        time_zone_offset = '-04:00'
        plant['post_datetime'] = ''.join([date_time, time_zone_offset])

        # Get the Taxon record for this Plant of the Day and collect
        # information to be used by the template.
        try:
            taxon = Taxon.objects.get(
                scientific_name=plant_record.scientific_name)
            plant['common_names'] = taxon.common_names.all()
            plant['facts'] = taxon.factoid
            plant['url'] = reverse('taxa-species',
                                   args=[taxon.genus.slug, taxon.epithet])

            image = None
            species_images = botany.species_images(taxon)
            if len(species_images) > 0:
                image = species_images[0]
            plant['image'] = image

            plants.append(plant)
        except ObjectDoesNotExist:
            pass

    return plants


def atom_view(request):
    MAX_NUMBER_PLANTS = 15
    partner_short_name = which_partner(request)

    plants_of_the_day = _get_plants_of_the_day(MAX_NUMBER_PLANTS,
                                               partner_short_name)

    return render_per_partner('atom.xml', {
            'plants_of_the_day': plants_of_the_day
        }, request, content_type='application/atom+xml')
