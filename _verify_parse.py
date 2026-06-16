from scraper import parse_products

HTML = """
<html><body>
  <article class="product_pod">
    <h3><a href="x.html" title="A Light in the Attic">A Light in the ...</a></h3>
    <p class="star-rating Three"></p>
    <div class="product_price"><p class="price_color">£51.77</p></div>
  </article>
  <article class="product_pod">
    <h3><a href="y.html" title="Tipping the Velvet">Tipping the Velvet</a></h3>
    <p class="star-rating One"></p>
    <div class="product_price"><p class="price_color">£53.74</p></div>
  </article>
  <article class="product_pod">
    <h3><a href="z.html" title="No Rating Book">No Rating Book</a></h3>
    <div class="product_price"><p class="price_color">£10.00</p></div>
  </article>
  <article class="product_pod">
    <h3><a href="w.html" title="Bad Rating Book">Bad Rating Book</a></h3>
    <p class="star-rating Nonsense"></p>
  </article>
</body></html>
"""

products = parse_products(HTML)
print("count:", len(products))
for p in products:
    print(p)
    assert set(p.keys()) == {"name", "price", "rating"}, "missing keys"
    assert p["rating"] == "N/A" or (isinstance(p["rating"], float) and 0.0 <= p["rating"] <= 5.0)

assert len(products) == 4
assert products[0] == {"name": "A Light in the Attic", "price": "£51.77", "rating": 3.0}
assert products[1] == {"name": "Tipping the Velvet", "price": "£53.74", "rating": 1.0}
assert products[2]["rating"] == "N/A"          # no star-rating element
assert products[3]["rating"] == "N/A"          # unreadable rating word
assert products[3]["price"] == "N/A"           # no price element

# Empty / no products
assert parse_products("<html><body><p>nothing</p></body></html>") == []
print("ALL CHECKS PASSED")
