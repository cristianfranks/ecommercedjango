$(document).ready(function () {
  function renderGalleryPreviews() {
    const galleryPreview = document.getElementById("gallery_preview");
    galleryPreview.innerHTML = "";

    galleryImages.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = function (e) {
        const img = document.createElement("img");
        img.src = e.target.result;
        img.style.maxWidth = "100px";
        img.style.margin = "10px";

        const deleteButton = document.createElement("button");
        deleteButton.innerText = "Delete";
        deleteButton.className = "btn btn-danger btn-sm";
        deleteButton.style.marginLeft = "10px";
        deleteButton.onclick = function () {
          galleryImages.splice(index, 1);
          renderGalleryPreviews();
        };

        const imgContainer = document.createElement("div");
        imgContainer.classList.add("col-4");
        imgContainer.appendChild(img);
        imgContainer.appendChild(deleteButton);

        galleryPreview.appendChild(imgContainer);
      };
      reader.readAsDataURL(file);
    });
  }

  document
    .getElementById("images")
    .addEventListener("change", function (event) {
      const productImagePreview = document.getElementById("image_preview");
      productImagePreview.innerHTML = "";

      const file = event.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          const img = document.createElement("img");
          img.src = e.target.result;
          img.style.maxWidth = "200px";
          img.style.margin = "10px";
          productImagePreview.appendChild(img);
        };
        reader.readAsDataURL(file);
      }
    });

  document
    .getElementById("gallery_image_input")
    .addEventListener("change", function (event) {
      const files = event.target.files;
      if (files.length > 0) {
        galleryImages.push(files[0]);
        renderGalleryPreviews();
      }
    });

  addExistingVariations();
});

function addExistingVariations() {
  var existingVariationsElement = document.getElementById("existingVariations");
  var existingVariationsValue = existingVariationsElement.getAttribute("value");

  variations = [];
  JSON.parse(existingVariationsValue).forEach((variation) => {
    variations.push(
      `${variation.fields.variation_category}:${variation.fields.variation_value}:${variation.fields.is_active}`
    );
  });
  renderVariationList();
}

function openDeleteGalleryModal(id) {
  $("#deleteGalleryForm").attr("action", `product_gallery_delete/${id}/`);
  $("#deleteGalleryForm")
    .off("submit")
    .on("submit", function (e) {
      e.preventDefault();
      $.ajax({
        url: $(this).attr("action"),
        type: "POST",
        data: $(this).serialize(),
        success: function (data) {
          if (data.success) {
            $("#deleteGalleryModal").modal("hide");
            $(".existing-image[data-image-id='" + id + "']").remove();
          } else {
            console.error("Delete failed");
          }
        },
        error: function (jqXHR, textStatus, errorThrown) {
          console.log(textStatus, errorThrown);
        },
      });
    });
}

function addVariation() {
  const category = document.getElementById("variation_category").value;
  const value = document.getElementById("variation_value").value;
  const isActive = document.getElementById("is_active").checked;

  if (category && value) {
    variations.push(`${category}:${value}:${isActive}`);
    renderVariationList();
  }
}

function renderVariationList() {
  const variationList = document.getElementById("variation_list");
  variationList.innerHTML = "";
  variations.forEach((variation, index) => {
    const [category, value, isActive] = variation.split(":");
    const div = document.createElement("div");
    div.classList.add("variation-item", "col-3", "mb-3");
    div.innerHTML = `<p>${category}: ${value}</p>
    <div class="form-check">
      <input class="form-check-input" type="checkbox" id="variation_active_${index}" name="variation_active_${index}" onchange="toggleVariationActive(${index}, this.checked)" ${
      isActive === "true" ? "checked" : ""
    }>
      <label class="form-check-label"  for="variation_active_${index}">Activo</label>
    </div>
    <button type="button" class="btn btn-danger" onclick="removeVariation(${index})">Eliminar</button>`;
    variationList.appendChild(div);
  });
}

function removeVariation(index) {
  variations.splice(index, 1);
  renderVariationList();
}

function toggleVariationActive(variationIndex, isActive) {
  variations.forEach((variation, index) => {
    const [category, value, _] = variation.split(":");
    if (index === variationIndex) {
      variations[index] = `${category}:${value}:${isActive}`;
    }
  });
}
