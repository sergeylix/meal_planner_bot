from meal_planner_bot.dishes import DishSeed


DISH_CATALOG = [
    DishSeed(
        name="Финская уха",
        slug="finnish_fish_soup",
        dish_type="суп",
        notes=(
            "Без обычной молочки. В вариантах заказа встречались кокосовое молоко и замена "
            "сливочного масла на гхи."
        ),
    ),
    DishSeed(
        name="Лазанья из кабачка",
        slug="zucchini_lasagna",
        dish_type="второе",
        notes="Также встречалась как кабачковая лазанья.",
    ),
    DishSeed(
        name="Слоеный салат с языком",
        slug="layered_tongue_salad",
        dish_type="салат",
        notes="Обычно заказывали без заправки.",
    ),
    DishSeed(
        name="Нутовые макароны с индейкой и овощами",
        slug="chickpea_pasta_with_turkey",
        dish_type="второе",
        notes="Иногда формулировалось как вок с нутовыми макаронами.",
    ),
    DishSeed(
        name="Салат с куриной печенью, хурмой и сыром",
        slug="chicken_liver_salad_with_persimmon",
        dish_type="салат",
        notes=(
            "В ранних вариантах были персик, креветки и лаймовый дрессинг. Позже закрепился вариант "
            "с хурмой; голубой сыр исключили, предпочтение отдавали фете, пармезану или козьему сыру."
        ),
    ),
    DishSeed(
        name="Суп-пюре из брокколи",
        slug="broccoli_cream_soup",
        dish_type="суп",
        notes="Варианты: на альтернативном или кокосовом молоке, иногда со шпинатом.",
    ),
    DishSeed(
        name="Мясные ежики с пшеном и цветной капустой",
        slug="meat_hedgehogs_with_millet",
        dish_type="второе",
        notes="Цветная капуста выступала гарниром.",
    ),
    DishSeed(
        name="Салат из индейки с хурмой, ягодами и фетой",
        slug="turkey_salad_with_persimmon",
        dish_type="салат",
        notes=(
            "Варианты: нектарины заменяли на хурму, ягоды были черникой или голубикой. "
            "Фета закрепилась как базовый сыр."
        ),
    ),
    DishSeed(
        name="Запеченное мясо с овощами",
        slug="baked_meat_with_vegetables",
        dish_type="второе",
    ),
    DishSeed(
        name="Суп на костном бульоне с овощами и мясом",
        slug="bone_broth_soup_with_meat",
        dish_type="суп",
        notes="Также встречался как костный бульон с овощами и мясом.",
    ),
    DishSeed(
        name="Печеночные оладьи",
        slug="liver_fritters",
        dish_type="второе",
    ),
    DishSeed(
        name="Тыквенный суп с чечевицей",
        slug="pumpkin_soup_with_lentils",
        dish_type="суп",
    ),
    DishSeed(
        name="Тыквенный крем-суп на кокосовом молоке",
        slug="pumpkin_cream_soup_with_coconut_milk",
        dish_type="суп",
    ),
    DishSeed(
        name="Рыбное суфле",
        slug="fish_souffle",
        dish_type="второе",
        notes=(
            "В разных заказах подавалось с бататом, картофелем, брокколи и зеленой спаржей. "
            "Был и вариант рыбно-шпинатного суфле."
        ),
    ),
    DishSeed(
        name="Салат цезарь с кальмарами и креветками",
        slug="caesar_salad_with_seafood",
        dish_type="салат",
        notes="Просили делать соус менее острым, с меньшим количеством чеснока и без сметаны или майонеза.",
    ),
    DishSeed(
        name="Овощное рагу с курицей",
        slug="chicken_vegetable_stew",
        dish_type="второе",
        notes=(
            "Базовые овощи: батат, картофель, морковь, кабачок, сладкий перец, черри, свекла. "
            "Иногда обсуждали добавление тыквы и цветной капусты."
        ),
    ),
    DishSeed(
        name="Суп лагман",
        slug="lagman_soup",
        dish_type="суп",
        notes="С говядиной и макаронами; просили меньше масла, жира и специй.",
    ),
    DishSeed(
        name="Салат с киноа и креветками",
        slug="quinoa_salad_with_shrimp",
        dish_type="салат",
        notes=(
            "Варианты включали брокколи, немного авокадо, гранат, ягоды, запеченные овощи, нут, "
            "черри и зелень. Иногда допускали немного феты или брынзы."
        ),
        recipe_url="https://howtogreen.ru/posts/926-salad/",
    ),
    DishSeed(
        name="Вок с гречневой лапшой и курицей",
        slug="buckwheat_noodles_wok_with_chicken",
        dish_type="второе",
        notes="Не острый, с увеличенным количеством овощей.",
    ),
    DishSeed(
        name="Рыбно-шпинатные котлеты с бататом и картофелем",
        slug="fish_spinach_cutlets",
        dish_type="второе",
    ),
    DishSeed(
        name="Салат с сулугуни и свеклой",
        slug="suluguni_beet_salad",
        dish_type="салат",
        notes=(
            "Добавляли зелень, редис и немного грецких орехов. Был вариант с жареным сулугуни."
        ),
    ),
    DishSeed(
        name="Борщ с говядиной",
        slug="beef_borscht",
        dish_type="суп",
        notes="Просили, чтобы мясо было мягким и его было не слишком много.",
    ),
    DishSeed(
        name="Оливье с ветчиной и кешью-соусом",
        slug="olivier_with_ham_and_cashew_sauce",
        dish_type="салат",
        notes="Кешью-соус просили подавать отдельно.",
        recipe_url="https://dzen.ru/a/XjAp1JhrOFMaVknU?utm_referrer=www.google.com&is_autologin_ya=true",
    ),
    DishSeed(
        name="Овощная лазанья",
        slug="vegetable_lasagna",
        dish_type="второе",
        notes="Просили без сливок и с альтернативным молоком вместо обычного.",
        recipe_url="https://eda.ru/recepty/pasta-picca/zapechennaja-ovoschnaja-lazanja-po-sredizemnomorski-18670",
    ),
    DishSeed(
        name="Салат с перепелиными яйцами и тунцом",
        slug="tuna_salad_with_quail_eggs",
        dish_type="салат",
        notes="Немного оливок, без дрессинга.",
        recipe_url="https://vkusvill.ru/media/recipes/salat-s-tuntsom-i-perepelinymi-yaytsami.html",
    ),
]
