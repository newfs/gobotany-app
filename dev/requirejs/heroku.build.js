/* RequireJS Build profile for production deployment to Heroku instance */
({
    appDir: '../../gobotany/static/scripts',
    dir: 'build',
    baseUrl: '.',
    mainConfigFile: '../../gobotany/static/scripts/require_config.js',

    findNestedDependencies: true,
    removeCombined: true,
    preserveLicenseComments: false,

    modules: [
        {
            name: 'gobotany.application',
            include: [
                'lib/require',

                'dkey/dkey',
                'editor/cv',
                'mapping/geocoder',
                'mapping/google_maps',
                'mapping/marker_map',
                'plantshare/delete_sighting',
                'plantshare/find_people',
                'plantshare/find_people_profile',
                'plantshare/manage_sightings',
                'plantshare/your_profile',
                'plantshare/plantshare',
                'plantshare/registration_complete',
                'plantshare/sightings_locator',
                'plantshare/sightings_locator_part',
                'plantshare/sightings_map',
                'plantshare/sign_up',
                'plantshare/new_sighting',
                'plantshare/new_checklist',
                'plantshare/edit_checklist',
                'plantshare/checklists',
                'simplekey/simple',
                'simplekey/results',
                'taxa/species',
                'taxa/family',
                'taxa/genus',
                'site/help',
                'site/advanced_map',
                'site/glossary',
                'site/species_list',
                'site/home',
                'site/maps_test',
                'util/suggester_init',
                'util/formset',
                'util/location_field_init'
            ],
            create: true
        }
    ]
})
