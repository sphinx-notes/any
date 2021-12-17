# sphinxnotes.any - Sphinx Domain for Descibing Anything

[

![image](https://img.shields.io/github/stars/sphinx-notes/any.svg?style=social&label=Star&maxAge=2592000)

](https://github.com/sphinx-notes/any)
* **version**

    2.2



* **copyright**

    Copyright ©2021 by Shengyu Zhang.



* **license**

    BSD, see LICENSE for details.


The extension provides a domain which allows user creates directive and roles to descibe, reference and index arbitrary object in documentation by writing reStructuredText templates. It is a bit like [`sphinx.application.Sphinx.add_object_type()`](https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_object_type), but more powerful.

## Installation

Download it from official Python Package Index:

```
$ pip install sphinxnotes-any
```

Add extension to `conf.py` in your sphinx project:

```
extensions = [
          # …
          'sphinxnotes.any',
          # …
          ]
```

## Configuration

The extension provides the following configuration:


### any_domain_name()

* **Type**

    `str`



* **Default**

    `'any'`


Name of the domain.


### any_schemas()

* **Type**

    `List[sphinxnotes.any.Schema]`



* **Default**

    `[]`


List of schema instances. For the way of writing schema definition, please refer to Defining Schema.

## Functionalities

### Defining Schema

The necessary python classes for writing schema are listed here:


### class any.Schema(objtype, name=Field(form=<Form.PLAIN: 1>, unique=True, referenceable=True, required=False), attrs={}, content=Field(form=<Form.PLAIN: 1>, unique=False, referenceable=False, required=False), description_template='{{ content }}', reference_template='{{ title }}', missing_reference_template='{{ title }} (missing reference)', ambiguous_reference_template='{{ title }} (disambiguation)')
Create a Schema instance.


* **Parameters**

    
    * **objtype** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – The unique type name of object, it will be used as
    basename of corresponding Directives, Roles and
    Indices


    * **name** (*any.schema.Field*) – Constraints of optional object name


    * **attrs** (*Dict**[*[*str*](https://docs.python.org/3/library/stdtypes.html#str)*, **any.schema.Field**]*) – Constraints of object attributes


    * **content** (*any.schema.Field*) – Constraints of object content


    * **description_template** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – See Description Template


    * **reference_template** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – See Reference Template


    * **missing_reference_template** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – See Reference Template


    * **ambiguous_reference_template** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – See Reference Template



* **Return type**

    [None](https://docs.python.org/3/library/constants.html#None)


Class-wide shared special keys used in template rendering context:


#### TYPE_KEY( = 'type')
Template variable name of object type


#### NAME_KEY( = 'name')
Template variable name of object name


#### CONTENT_KEY( = 'content')
Template variable name of object content


#### TITLE_KEY( = 'title')
Template variable name of object title


### class any.Field(form=Form.PLAIN, unique=False, referenceable=False, required=False)
Describes value constraint of field of Object.

The value of field can be single or mulitple string.


* **Parameters**

    
    * **form** (*any.schema.Field.Form*) – The form of value.


    * **unique** ([*bool*](https://docs.python.org/3/library/functions.html#bool)) – Whether the field is unique.
    If true, the value of field must be unique within the scope of objects
    with same type. And it will be used as base string of object
    identifier.

    Only one unique field is allowed in one object type.

    **NOTE**: Duplicated value causes a warning when building documentation,
    and the corresponding object cannot be referenced correctly.



    * **referenceable** ([*bool*](https://docs.python.org/3/library/functions.html#bool)) – Whether the field is referenceable.
    If ture, object can be referenced by field value.
    See Roles for more details.


    * **required** ([*bool*](https://docs.python.org/3/library/functions.html#bool)) – Whether the field is required.
    If ture, `ObjectError` will be raised when building documentation
    if the value is no given.



* **Return type**

    [None](https://docs.python.org/3/library/constants.html#None)



### class any.Field.Form(value)
An enumeration represents various string forms.


#### PLAIN( = 1)
A single string


#### WORDS( = 2)
Mulitple string separated by whitespace


#### LINES( = 3)
Mulitple string separated by newline(`\\n`)

### Documenting Object

Once a schema created, the corresponding Directives, Roles and Indices will be generated. You can use them to descibe, reference and index object in your documentation.

For the convenience, we use default domain name “any”, and we assume that we have the following schema with in `⚙️any_schemas`:

```
from textwrap import dedent
from any import Schema, Field

cat = Schema('cat',
    name=Field(referenceable=True, form=Field.Form.LINES),
    attrs={
        'id': Field(unique=True, referenceable=True, required=True),
        'color': Field(referenceable=True),
        'picture': Field(),
    },
    description_template=dedent("""
        .. image:: {{ picture }}
           :align: left

        :Cat ID: {{ id }}
        :Color: {{ color }}

        {{ content }}"""),
    reference_template='🐈{{ title }}',
    missing_reference_template='😿{{ title }}',
    ambiguous_reference_template='😼{{ title }}')
```

#### Directives

##### Object Description

The aboved schema created a [Directive](https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#directives) named with “`domain`:`objtype`” (In this case, it is `any:cat`) for descibing object(INC, it is cat🐈).

Arguments

    Arguments are used to specify the `{{name}}` of the object. The number argument is depends on the name `any.Field` of Schema.


    * A `None` field means no argument is required


    * For a non-`None` Field, see `any.Field` for more details

    Specially, If first argument is `_` (underscore), the directive must be located after a [Section Title](https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#sections), the text of section title is the real first argument.

    In this case, the `any:cat` directive accepts multiple argument split by newline.

Options

    All attributes defined in schema are converted to options of directive. Further, they will available in various Templates.


    * A `None` field is no allowed for now means no argument is required


    * For a non-`None` Field, see `any.Field` for more details

    In this case, the directive has three options: `id`, `color` and `picture`.

Content

    Content is used to specify the `{{content}}` of the object.


    * A `None` field means no content is required


    * for a non-`none` field, see `any.field` for more details

    in this case, the directive accepts content.

the directive will be rendered to a restructuredtext snippet, by Description Template, then inserted to documentation.

Let’s documenting such a cat:

```
.. any:cat:: Nyan Cat
             Nyan_Cat
   :id: 1
   :color: pink gray
   :picture: _images/nyan-cat.gif

   Nyan Cat is the name of a YouTube video uploaded in April 2011,
   which became an internet meme. The video merged a Japanese pop song with
   an animated cartoon cat with a Pop-Tart for a torso, flying through space,
   and leaving a rainbow trail behind it. The video ranked at number 5 on
   the list of most viewed YouTube videos in 2011. [#]_

   .. [#] https://en.wikipedia.org/wiki/Nyan_Cat
```

It will be rendered as:


### Nyan Cat()


![image](_images/nyan-cat.gif)


* **Cat ID**

    1



* **Color**

    pink gray


Nyan Cat is the name of a YouTube video uploaded in April 2011,
which became an internet meme. The video merged a Japanese pop song with
an animated cartoon cat with a Pop-Tart for a torso, flying through space,
and leaving a rainbow trail behind it. The video ranked at number 5 on
the list of most viewed YouTube videos in 2011. 

#### Roles

Same to [Cross-referencing syntax](https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#xref-syntax), explicit title `:role:\`title <target>\`` is supported by all the [Role](https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#interpreted-text)s. If not explicit title specific, reference title will be rendered by one of Reference Template.

##### General Reference

The aboved schema created a role named with “`domain`-`objtype`” (In this case, it is `any:cat`) for creating a reference to Object Description. The interpreted text can be value of *any referenceable field*.

| Reference by name

 | `:any:cat:\`Nyan Cat\``

 | `🐈Nyan Cat`

 |
| By another name

   | `:any:cat:\`Nyan_Cat\``

 | `🐈Nyan Cat`

 |
| By ID

             | `:any:cat:\`1\``

        | `🐈Nyan Cat`

 |
| Explicit title

    | `:any:cat:\`This cat <Nyan Cat>\``

 | `This cat`

  |
| A nonexistent cat

 | `:any:cat:\`mimi\``

                | `😿mimi`

     |
##### Field-Specific Reference

Role “`domain`-`objtype`.`field`” will be created for all referenceable Fields (In this case, it is `any:cat.name`, `any:cat.id` and `any:cat.color`).

These roles also create reference to Object Description. But the interpreted text must be value of field in role’s name.

| Reference by name

 | `:any:cat.name:\`Nyan Cat\``

       | `🐈Nyan Cat`

 |
| By ID

             | `:any:cat.id:\`1\``

                | `🐈Nyan Cat`

 |
#### Indices

According to sphinx documentation, we use [Cross-referencing arbitrary locations](https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#ref-role) to create reference to object indices, and the index name should prefixed with domain name.

##### General Index

Index “`domain`-`objtype`” (In this case, it is `any-cat`) creates reference to object index which grouped by all referenceable field values.

| `:ref:\`any-cat\``

    | Cat Reference Index

            |
##### Field Specific Index

Index “`domain`-`objtype`.`field`” will be created for all reference Fields (In this case, it is `any-cat.name`, `any-cat.id` and `any-cat.color`).

These indices create reference to object index which grouped by specific field values.

| `:ref:\`any-cat.name\``

 | Cat Name Reference Index

       |
| `:ref:\`any-cat.id\``

   | Cat Id Reference Index

         |
### Writing Template

We use [Jinja](https://jinja.palletsprojects.com/) as our templating engine.

Currently we need two kinds of template to let .

#### Description Template

Used to generate object description. Can be written in reStructuredText.

#### Reference Template

Used to generate object reference. Only plain text is allowed for now.

Reference Template has two various variants:

Missing Reference Template

    Applied when the reference is missing.

Ambiguous Reference Template

    Applied when the reference is ambiguous.

#### Variables

For the usage of Jinja’s variable, please refer to [Jinja’s Variables](<https://jinja.palletsprojects.com/en/2.11.x/templates/#variables).

All attributes defined in schema are available as variables in template. Note the value of variable might be *string or string list* (depends on value of `any.Schema.Field.Form`).

Beside, there are some special variable:


### objtype()

* **Type**

    `str`


Type of object.


### name()

* **Type**

    `Union[None,str,List[str]]`


Name of object.


### content()

* **Type**

    `Union[None,str,List[str]]`


Content of object.


### title()

* **Type**

    `str`


Title of object.

In Reference Template, its value might be overwritten by explicit title.

#### Filters

For the usage of Jinja’s filter, please refer to [Jinja’s Filters](https://jinja.palletsprojects.com/en/2.11.x/templates/#filters>).

All [Jinja’s Builtin Filters](https://jinja.palletsprojects.com/en/2.11.x/templates/#builtin-filters) are available.
In additional, we provide the following custom filters to enhance the template:

`copyfile(fn)`

    Copy a file in Sphinx srcdir to outdir, return the URI of file which relative
    to current documentation.

    The relative path to srcdir will be preserved, for example,
    `{{ fn | copyfile }}` while `fn` is `_images/foo.jpg`,
    the file will copied to `<OUTDIR>/_any/_images/foo.jpg`, and returns
    a POSIX path of `fn` which relative to current documentation.

`thumbnail(img, width, height)`

    > Changes the size of an image to the given dimensions and removes any
    > associated profiles, returns a a POSIX path of thumbnail which relative to
    > current documentation.

    > This filter always keep the origin aspect ratio of image.
    > The width and height are optional, By default are 1280 and 720 respectively.

    **Versionadded:** New in version 1.0.

## Tips

### Omit Domain Name

You can omit the prefixed domain name in directives and roles by setting the `primary_domain` to your `⚙️any_domain_name` in `conf.py`. For example, you can use `.. cat::` rather than `.. any:cat::`.

### Documenting Section and Documentation

By using the Underscore Argument, you can
document a section and reference to it. For example:

```
================
The Story of Art
================

.. book:: _
   :publisher: Phaidon Press; 16th edition (April 9, 1995)
   :isbn: 0714832472
   :language: English
```

You not need to create a reST label by yourself, just use role like `:book:\`The Story of Art\``. Beside, it is also a better replacement of  [Bibliographic Fields](https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#bibliographic-fields).

### Enrich Object Description

As the Description Template supports reStructuredText, We have a lot of room to play.

#### Categorizing and Tagging

When we descibing a object, usually we are categorizing and tagging them.
For dog, we may define such a Schema:

```
from textwrap import dedent
from any import Schema, Field

dog = Schema('dog',
    attrs={
        'breed': Field(referenceable=True),
        'color': Field(referenceable=True, form=Field.Form.WORDS),
    },
    description_template=dedent("""
        :Breed: {{ breed }}
        :Colors: {{ colors }}"""),
    reference_template='🐕{{ title }}',
    ambiguous_reference_template='{{ title }}')
```

The field `breed` is a category and `colors` is a serial of tags.  We are really categorizing and tagging dogs but, it is a quite boring.  Considering the following object description:

```
.. any:dog:: Indiana
   :breed: Husky
   :color: Black White
```

When we see the breed of Indiana is “Husky”, we may want to see what other huskies. When we see the colors of Indiana is “Black” and “White”, We will have the same idea. So, let’s create references for these values:

```
from textwrap import dedent
from any import Schema, Field

dog = Schema('dog',
    attrs={
        'breed': Field(referenceable=True),
        'color': Field(referenceable=True, form=Field.Form.WORDS),
    },
    description_template=dedent("""
        :Breed: :any:dog.breed:`{{ breed }}`
        :Colors: {% for c in color %}:any:dog.color:`{{ c }}` {% endfor %}"""),
    reference_template='🐕{{ title }}',
    ambiguous_reference_template='{{ title }}')
```

For field breed, its value is a string, so we simpily wrap value in to a `any:dog.breed` role, In this case it create a reference to all Husky dog.

For field color, its value is a string list, we have to iterate it and wrap element to to a `any:dog.color` role, In this case it create a reference to all Black dog and White dog.

The rendered reStructuredText looks like this:

```
:Breed: :any:dog.breed:`Husky`
:Colors: :any:dog.color:`Black` any:dog.color:`White`
```

The rendered object description:


### Indiana()

* **Breed**

    `Husky`



* **Colors**

    `Black` `White`


## Change Log

### 2021-08-18 2.2


* Use the Object ID as index name when no object title available

### 2021-06-26 2.1


* Report ambiguous object via debug log


* Some doc fixes


* Remove unused import

### 2021-06-05 2.0


* Update documentation, add some tips

### 2021-06-03 2.0a3


* Simplify index name (e4d9207)

### 2021-06-03 2.0a3


* Simplify index name (e4d9207)

### 2021-05-23 2.0a2


* Fix none object signture (6a5f75f)


* Prevent sphinx config changed everytime (f7b316b)

### 2021-05-23 2.0a1


* Template variable must be non None (fb9678e)


* Template will not apply on role with explicit title (5bdaad1)

### 2021-05-22 2.0a0


* Descibing schema with python object instead of dict


* Support index


* Refactor

### 2021-02-28 1.1


* Remove symbol link if exists

### 2021-02-23 1.0


* Move preset schemas to standalone package


* Add custom filter support to template


* Combine `any_predefined_schemas` and `any_custom_schemas` to `any_schemas`

### 2021-01-28 1.0b0


* Fix the missing Jinja dependency


* Use section title as object name when directive argument is omitted


* Some code cleanups


* Rename schema field “role” to “reference”


* Rename schema field “directive” to “content”

### 2020-12-20 1.0a1

The alpha version is out, enjoy~
