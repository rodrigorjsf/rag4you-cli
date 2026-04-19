# PolarQuant: Quantizing KV Caches with Polar Transformation

Insu Han Praneeth Kacham Amin Karbasi KAIST Google Research Yale University `insu.han@kaist.ac.kr pkacham@google.com amin.karbasi@yale.edu`

Vahab Mirrokni Amir Zandieh Google Research Google Research `mirrokni@google.com zandieh@google.com`

## **Abstract**

Large language models (LLMs) require significant memory to store Key-Value (KV) embeddings in their KV cache, especially when handling long-range contexts. Quantization of these KV embeddings is a common technique to reduce memory consumption. This work introduces PolarQuant, a novel quantization method employing random preconditioning and polar transformation. Our method transforms the KV embeddings into polar coordinates using an efficient recursive algorithm and then quantizes resulting angles. Our key insight is that, after random preconditioning, the angles in the polar representation exhibit a tightly bounded and highly concentrated distribution with an analytically computable form. This nice distribution eliminates the need for explicit normalization, a step required by traditional quantization methods which introduces significant memory overhead because quantization parameters (e.g., zero point and scale) must be stored in full precision per each data block. PolarQuant bypasses this normalization step, enabling substantial memory savings. The long-context evaluation demonstrates that PolarQuant compresses the KV cache by over _×_ **4** _._ **2** while achieving the best quality scores compared to the state-of-the-art methods.

## **1 Introduction**

Transformer-based models form the backbone of modern artificial intelligence systems and have been instrumental in driving the ongoing AI revolution. Their applications span various domains, including frontier language models (LLM) [1, 3, 15] to text-to-image [32, 12, 28], text-to-video synthesis [16, 30], coding assistants [27] and even multimodal models that ingest text, audio, image, and video data [29, 15]. The self-attention mechanism [37] is at the heart of these models as it enables capturing the direct dependencies of all tokens in the input sequence. The ability of these models grows along with their size and context length [21], which leads to computational challenges in terms of huge memory consumption to support fast inference.

> *Authors are listed alphabetically.

Most large language models, as well as multimodal and video models, adopt an autoregressive, decoder-only architecture that generates tokens sequentially. To avoid redundant attention score computations during the generation phase, these models employ a KV caching scheme, which stores the key and value embeddings of previously generated tokens in each attention layer. However, a significant challenge in deploying autoregressive Transformers lies in the substantial memory demands, as the KV cache size scales with both the model size (i.e., the number of layers and attention heads) and the context length. Furthermore, serving each model session typically necessitates its own dedicated KV cache, further compounding memory demands. This has become a significant bottleneck in terms of memory usage and computational speed, particularly for models with long context lengths. Thus, reducing the KV cache size while preserving accuracy is critical to addressing these limitations.

Several approaches have been proposed to address the KV caching challenge. Architectural solutions, such as multi-query attention [34], grouped-query attention [2], and multi-head latent attention [9], modify the transformer architecture to reduce the memory demands during inference by decreasing the _number_ of key-value pairs that are to be stored.

Another orthogonal line of research focuses on reducing the KV cache size by pruning or evicting redundant or unimportant tokens [6, 44, 25, 38, 42, 24]. However, eviction strategies face limitations in long-context tasks that require precise knowledge extraction, such as needle-in-haystack scenarios. Additionally, some recent works tackle the issue from a systems perspective, such as offloading [35, 36] or integrating virtual memory and paging strategies into the attention mechanism [23].

A simple yet effective approach to reducing KV cache size is quantizing the floating-point numbers (FPN) in the KV cache by storing their approximations using fewer number of bits. Several quantization methods have been proposed specifically for the KV cache [40, 39, 11, 20, 43, 26, 17]. Recently, a new KV cache quantization method called QJL [41] introduced an efficient, data-oblivious 1-bit quantization approach based on sketching techniques. This method does not require tuning or adaptation to the input data, incurs significantly lower memory overhead compared to prior works, and achieves superior performance. A very recent work, Lexico [22], applies techniques from sparse representation learning to compress the KV cache by learning a universal dictionary such that all key and value embeddings are represented as extremely sparse vectors within the learned dictionary. Unfortunately, this approach requires solving a computationally expensive matching pursuit algorithm for each key and value embedding, making Lexico relatively slow.

Traditional KV cache quantization methods face significant “memory overhead” due to the need for data normalization before quantization. Most methods group data into blocks–either channelwise or token-wise–and independently normalize each block which requires computing and storing quantization constants (e.g., zero points and scales) in full precision. This process can add over 1 additional bit per quantized number, resulting in considerable memory overhead. We show that applying a random preconditioning matrix on the embedding vectors eliminates the need for data normalization. This approach aligns with the recent use of random Hadamard matrices as preconditioners before quantizing embedding vectors in attention layers to improve quality [33, 4].

## **1.1 Contributions**

We propose quantizing KV vectors in polar coordinates instead of the usual Cartesian coordinates. This shift enables more efficient representation and compression of KV embeddings.

**Random Preconditioning.** We apply a random rotation to the vectors before quantization, which preserves inner products while randomizing the distribution of each vector. This preconditioning causes the angles in polar coordinates to concentrate, allowing us to quantize them with high precision using small bit-widths. We derive the analytical distribution of angles after preconditioning and leverage this insight to construct an optimized quantization codebook, minimizing quantization error.

**Recursive Polar Transformation.** We introduce a computationally efficient recursive polar transformation that converts vectors into polar coordinates, enabling practical deployment of our approach. We are able to prove an error bound in Theorem 1 showing our algorithm is asymptotically optimal for worst-case KV embedding vectors.

**Performance on Long-Context Tasks.** We evaluate PolarQuant on long-context tasks and demonstrate that it achieves the best quality scores compared to competing methods while compressing the KV cache memory by over _×_ **4** _._ **2** .

## **2 Preliminaries**

We use boldface lowercase letters, such as _**x**_ and _**y**_ , to denote vectors, and boldface uppercase letters, like _**M**_ , to denote matrices. To denote a slice of a vector _**x**_ between the coordinate indices _i_ and _j_ inclusive of the endpoints, we use the notation _**x** i_ : _j_ . For a matrix _**M**_ , we write _**M** i,_ : to denote its _i_ -th row vector, which we will simply refer to as _**M** i_ .

## **2.1 Efficient Token Generation and KV Caching**

Autoregressive Transformers often utilize cache storage for faster token generation. Given an input prompt, models encode the prompt information into two types of embeddings, called Key and Value. To generate subsequence tokens efficiently, the Key-Value (KV) embeddings are cached to avoid recomputing them.

The Key-Value (KV) caching method leverages the architecture of transformer decodcers, where a causal mask in applied in the attention mechanism. Once the keys and values are computed for a given token, they remain unchanged for subsequent token generation. By caching these key-value pairs, the model avoids redundant computations, as it only needs to compute the query for the current token and reuse the cached keys and values for attention.

This approach significantly reduces computation time during token generation. Instead of processing the entire sequence repeatedly, the KV cache enables the model to efficiently focus on the incremental computation of new tokens. This makes the method particularly useful in real-time applications, such as conversational AI and text generation, where fast and resource-efficient inference is critical.

**==> picture [424 x 153] intentionally omitted <==**

**----- Start of picture text -----**<br>
x  ∈ R [d] ψ [(1)] ∈ R [d/] [2] ψ [(2)] ∈ R [d/] [4]<br>x 1:2<br>r 1 [(1)] r [(1)] ∈ R [d/] [2]<br>x 1:2 ψ 1 [(1)]<br>r 1 [(1)] r 1:2 [(1)] r [(log][2] [ d] [)] ∈ R<br>x 3:4 r 2 [(1)] ψ 2 [(1)] x 3:4 r 2 [(1)] . .. r 1 [(2)] ψ 1 [(2)]<br>...<br>...<br>x d− 1: d xr dd/ [(1)] − 1:2 d ψd/ [(1)] 2 r d/ [(1)] 2 : transformed: original inputinputin Cartesianin Polar<br>...<br>...<br>**----- End of picture text -----**<br>

Figure 1: Overview of recursive polar transformation procedure in Definition 1

## **2.2 Random Preconditioning**

A critical step in the PolarQuant algorithm is random preconditioning of the KV vectors prior to quantization. This involves applying a random projection matrix to the embedding vectors before quantizing them. To analyze the algorithm effectively, we rely on specific facts and properties of multivariate normal random variables, which are outlined below.

**Fact 1.** _For any positive integer d, if_ _**x** ∈_ R _[d] is a zero mean unit variance isotropic Gaussian random variable in dimension d, i.e.,_ _**x** ∼N_ (0 _,_ _**I** d_ ) _, then its_ 2 _-norm, denoted by r_ := _∥_ _**x** ∥_ 2 _, follows a generalized gamma distribution with the following probability density for any r ≥_ 0 _:_

**==> picture [184 x 26] intentionally omitted <==**

The proof of Fact 1 is provided in Appendix A. We also use the following facts about the moments of the univariate normal distribution.

**Fact 2** (Moments of Normal Random Variable) **.** _If x is a normal random variable with zero mean and unit variance x ∼N_ (0 _,_ 1) _, then for any integer ℓ,_ E _x∼N_ (0 _,_ 1) � _|x|[ℓ]_[�] = 2 _[ℓ/]_[2] Γ(( _ℓ_ + 1) _/_ 2) _/[√] π._

PolarQuant algorithm applies a random preconditioning prior to quantization. This preconditioning involves multiplying each embedding vector by a shared random sketch matrix _**S**_ with i.i.d. normal entries. By the Johnson-Lindenstrauss (JL) lemma [10], this preconditioning preserves the norms and inner products of the embedding vectors with minimal distortion. A key property of this preconditioning, which we will leverage in our later analysis, is that the embedding vectors after preconditioning follow a multivariate normal distribution. This is formalized in the following fact.

**Fact 3.** _For any vector_ _**x** ∈_ R _[d] if_ _**S** ∈_ R _[m][×][d] is a random matrix with i.i.d. normal entries_ _**S** i,j ∼N_ (0 _,_ 1) _, then the vector_ _**S** ·_ _**x** has multivariate normal distribution_ _**S** ·_ _**x** ∼N_ (0 _, ∥_ _**x** ∥_ 2 _·_ _**I** m_ ) _._

The following lemma establishes the distribution of the polar angle of a point ( _x, y_ ) in dimension 2, where the _x_ and _y_ coordinates are independent samples from the Euclidean norm of multivariate normal random variables.

**Lemma 1.** _For any positive integer d, if x, y ≥_ 0 _are two i.i.d. random variables with generalized gamma distribution with probability density function fZ_ ( _z_ ) = 2 _[d/]_[2] _·_ Γ(2 _d/_ 2) _[z][d][−]_[1][ exp] � _−z_[2] _/_ 2� _, then the angle variable θ_ := tan _[−]_[1] ( _y/x_ ) _follows the probability density function:_

**==> picture [170 x 27] intentionally omitted <==**

_Additionally,_ E[Θ] = _π/_ 4 _and_ Var(Θ) = _O_ (1 _/√d_ ) _._

See Appendix B for a proof.

## **3 PolarQuant**

We now describe our approach of quantizing angles in polar coordinates and using it to the KV cache problem. In Section 3.1, we introduce how to recursively transform Cartesian vector to polar coordinates. In Section 3.2, we provide an analysis of polar angle distributions with preconditioning. In Section 3.3, we explain details of quantization polar transformed embeddings and practical implementation.

## **3.1 Recursive Polar Transformation**

There are various methods to derive the polar representation of R _[d]_ . Here we propose a polar transformation that can be recursively computed from the Cartesian coordinates of points in R _[d]_ . Throughout this work, we assume that _d_ is an integer power of 2.

At a high level, our approach begins by grouping pairs of coordinates of a _d_ -dimensional vector _**x**_ and transforming each pair into 2D polar coordinates. This produces _d/_ 2 radius and angle pairs. Next, we gather _d/_ 2 of radii and apply the polar transform to them. This procedure is recursively repeated log2 _d_ times and the final output consists of a single final radius and a collection of 1 _,_ 2 _,_ 4 _, . . . , d/_ 2- dimensional angle vectors. A formal definition is provided in Definition 1.

**Definition 1** (Cartesian to Polar Transformation) **.** _For any integer power of two d, the polar representation of any vector_ _**x** ∈_ R _[d] includes d −_ 1 _angles and a radius. Angles are organized into a collection of_ log2 _d vector of angles ψ_[(1)] _, ψ_[(2)] _, . . . ψ_[(log][2] _[ d]_[)] _such that ψ_[(1)] _∈_ [0 _,_ 2 _π_ ) _[d/]_[2] _and ψ_[(] _[ℓ]_[)] _∈_ [0 _, π/_ 2] _[d/]_[2] _[ℓ] for any ℓ ≥_ 2 _. In other words, the angles are computed in_ log2 _d levels and there are d/_ 2 _[ℓ] angles in level l. These angles are defined by the following relation for ℓ ∈{_ 2 _,_ 3 _, . . ._ log2 _d}:_

**==> picture [272 x 65] intentionally omitted <==**

_The reverse of this transformation maps the angles and the radius of any point to its Cartesian_

_vector representation using the following equation:_

**==> picture [367 x 35] intentionally omitted <==**

A visual diagram of the algorithm is shown in Fig. 1 and the pseudocode is provided in Algorithm 1 (see Polar procedure). In what follows, we analyze the distribution of angles generated in each quantization level.

## **3.2 Distribution of Polar Angles Under Random Preconditioning**

One of our primary objectives is to eliminate the need for explicit normalization (e.g., minimum/maximum values) of the KV cache data prior to quantization, thereby reducing quantization overhead. To achieve this, our algorithm applies random preconditioning to the embedding vectors. This preconditioning involves multiplying each embedding vector by a shared random sketch matrix _**S**_ with i.i.d. normal entries. By the Johnson-Lindenstrauss (JL) lemma [10], this preconditioning preserves the norms and inner products[*] of the embedding vectors with minimal distortion. A key property of this preconditioning, which we will leverage in our later analysis, is that the embedding vectors after preconditioning follow a multivariate normal distribution. This has been formalized in Fact 3.

During the preconditioning stage, the sketch is applied to all embedding vectors in the KV cache, allowing the analysis of PolarQuant to effectively treat the vectors being quantized as samples from a multivariate normal distribution. So for the analysis and design of PolarQuant we can assume without loss of generality that our goal is to quantize a random vector with multivariate Gaussian distribution. A critical insight is that the distribution of angles after random preconditioning becomes predictable and can be analytically derived, which enables the design of optimal quantization schemes.

The polar distribution of a Gaussian vector is derived in the following lemma.

**Lemma 2** (Distribution of a Gaussian Vector Under Polar Transformation) **.** _For an integer power of two d, suppose that_ _**x** ∼N_ (0 _, Id_ ) _is a random zero mean isotropic Gaussian random variable in dimension d. Let ψd_ ( _**x**_ ) := � _ψ_[(1)] _, ψ_[(2)] _, . . . ψ_[(log][2] _[ d]_[)][�] _denote the set of polar angles obtained by applying the polar transformation defined in Definition 1 on_ _**x** . Denote the radius of_ _**x** by r_ = _∥_ _**x** ∥_ 2 _. The joint probability density function for_ � _r, ψ_[(1)] _, ψ_[(2)] _, . . . ψ_[(log][2] _[ d]_[)][�] _is the following:_

**==> picture [337 x 35] intentionally omitted <==**

_where fR_ ( _r_ ) _is the p.d.f. defined in Fact 1, f_ Ψ(1) _is p.d.f. of the uniform distribution over_ [0 _,_ 2 _π_ ) _[d/]_[2] _:_

**==> picture [136 x 15] intentionally omitted <==**

> * For our implementation, we use random rotation matrices (square matrices _P_ satisfying _P ⊤P_ = _I_ ), which preserve the norms and inner products exactly while removing the independence across projected coordinates which we use for our theoretical results.

_and for every ℓ ∈{_ 2 _,_ 3 _, . . ._ log2 _d} the p.d.f. f_ Ψ( _ℓ_ ) _is the following:_

**==> picture [236 x 56] intentionally omitted <==**

_Proof._ The proof is by induction on _d_ . First for the base of induction we prove the result in dimension _d_ = 2. So we prove that for a 2-dimensional random Gaussian vector _**y**_ = ( _y_ 1 _, y_ 2) _∈_ R[2] if ( _r, θ_ ) is the polar representation of this vector then following holds:

**==> picture [152 x 23] intentionally omitted <==**

To prove this, let _fY_ ( _**y**_ ) be the probability density function of the vector random variable _**y**_ . We know _**y**_ has a normal distribution so we have:

**==> picture [248 x 25] intentionally omitted <==**

where the first equality above follows from the change of variable from ( _y_ 1 _, y_ 2) to _r_ = ~~�~~ _y_ 1[2][+] _[ y]_ 2[2][and] _θ_ = tan _[−]_[1] ( _y_ 2 _/y_ 1). This proves the base of induction for _d_ = 2.

Now we prove the inductive step. Suppose that the lemma holds for dimension _d/_ 2 and we want to log2 _d−_ 1 log2 _d−_ 1 prove it for dimension _d_ . Denote _θ_ := _ψ_[(log][2] _[ d]_[)] , _**ϕ**_ 1 := � _ψ_ 1:[(] _[l]_[)] _d/_ 2 _[l]_[+1] � _ℓ_ =1 , _**ϕ**_ 2 := � _ψd/_[(] _[l]_[)] 2 _[ℓ]_[+1] +1: _d/_ 2 _[ℓ]_ � _ℓ_ =1 , _r_ 1 := �� _**x**_ 1: _d/_ 2��, and _r_ 2 := �� _**x** d/_ 2+1: _d_ ��. Essentially we sliced all the angle vectors _ψ_ ( _ℓ_ ) in half and named the collection of first half vectors _**ϕ**_ 1 and the collection of second halves _**ϕ**_ 2. Using the definition of _ψ_[(] _[ℓ]_[)] ’s in Definition 1, _**ϕ**_ 1 is exactly the polar transformation of _**x**_ 1: _d/_ 2, and _**ϕ**_ 2 is the polar transformation of _**x** d/_ 2+1: _d_ , so by the definition of _ψd_ ( _**x**_ ) in the lemma statement we have _**ϕ**_ 1 = _ψd/_ 2( _**x**_ 1: _d/_ 2) and _**ϕ**_ 2 = _ψd/_ 2( _**x** d/_ 2+1: _d_ ). Thus, we can write: _fR,_ Ψ _d_ ( _r, ψd_ ( _**x**_ )) = _fR,_ Θ _,_ Φ1 _,_ Φ2( _r, θ,_ _**ϕ**_ 1 _,_ _**ϕ**_ 2) = _r · fR_ 1 _,R_ 2 _,_ Φ1 _,_ Φ2( _r_ cos _θ, r_ sin _θ,_ _**ϕ**_ 1 _,_ _**ϕ**_ 2) = _r · fR_ 1 _,_ Φ1( _r_ cos _θ,_ _**ϕ**_ 1) _· fR_ 2 _,_ Φ2( _r_ sin _θ,_ _**ϕ**_ 2) = _r · fR,_ Ψ _d/_ 2( _r_ 1 _,_ _**ϕ**_ 1) _· fR,_ Ψ _d/_ 2( _r_ 2 _,_ _**ϕ**_ 2) _,_ (2) where the third line above follows from the change of variable from ( _r_ 1 _, r_ 2) = ( _r_ cos _θ, r_ sin _θ_ ) to _r_ = ~~�~~ _r_ 1[2][+] _[ r]_ 2[2][and] _[θ]_[=][tan] _[−]_[1][(] _[r]_[2] _[/r]_[1][).] In the fourth line above we used the definition of _θ_ = _ψ_[(log][2] _[ d]_[)] = tan _[−]_[1] � _∥∥_ _**xx** d/_ 1:2+1: _d/_ 2 _∥d∥_ 2 2 � from Definition 1.

Now if we let _f_ Ψ _d/_ 2( _**ϕ**_ 1) :=[�][log] _ℓ_ =1[2] _[ d][−]_[1] _f_ Ψ( _ℓ_ ) � _ψ_ 1:[(] _[ℓ] d/_[)] 2 _[ℓ]_[+1] � and _f_ Ψ _d/_ 2( _**ϕ**_ 2) :=[�] _ℓ_[log] =1[2] _[ d][−]_[1] _f_ Ψ( _ℓ_ ) � _ψd/_[(] _[ℓ]_[)] 2 _[ℓ]_[+1] +1: _d/_ 2 _[ℓ]_ �, by the inductive hypothesis we have _fR,_ Ψ _d/_ 2( _r_ 1 _,_ _**ϕ**_ 1) = 2 _[d/]_[4] _·_ Γ(2 _d/_ 4) _[r]_ 1 _[d/]_[2] _[−]_[1] exp � _−r_ 1[2] _[/]_[2] � _· f_ Ψ _d/_ 2( _**ϕ**_ 1) and

**==> picture [472 x 19] intentionally omitted <==**

**==> picture [395 x 110] intentionally omitted <==**

which completes the inductive proof of this lemma.

Lemma 2 demonstrates that the angles of Gaussian vectors in polar coordinates have independent distributions, as the probability density function is separable. Moreover, all angles within the same level share identical distributions. Specifically, at level _ℓ_ all angles follow the distribution _ψi_[(] _[ℓ]_[)] _∼ d/_ 2 _ℓ_ Γ(2 _[ℓ][−]_[1] ) � _i_ =1 2[2] _[ℓ][−]_[1] _[−]_[2] _·_ Γ[2 _[ℓ][−]_[2] ](2)[sin][2] _[ℓ][−]_[1] _[−]_[1][ �] 2 _ψi_[(] _[ℓ]_[)] �. This density becomes increasingly concentrated around _π/_ 4, particularly at higher levels _ℓ_ . This property is highly beneficial for reducing quantization error for the angles at higher levels.

## **3.3 PolarQuant Algorithm and Main Theorem**

PolarQuant starts by first applying random preconditioning, then transforming the vectors into polar coordinates, and finally quantizing each angle. Since Lemma 2 shows that the angles in polar coordinates are independent random variables, each angle can be quantized independently to minimize the total mean squared error. Jointly quantizing multiple angle coordinates offers no additional benefit due to their independence, making our approach both computationally efficient and effective. Therefore, we can focus on one angle at level _l_ and design optimal quantization scheme for it so as to minimize the mean squared error.

Consider an angle _ψi_[(] _[ℓ]_[)] at some level _ℓ_ . According to Lemma 2, its values lie within the range [0 _, π/_ 2] for _ℓ ≥_ 2 and for _ℓ_ = 1 it takes values in the range [0 _,_ 2 _π_ ) with a probability density function given Γ(2 _[ℓ][−]_[1] ) by _fℓ_ ( _ψi_[(] _[ℓ]_[)][) :=] 2[2] _[ℓ][−]_[1] _[−]_[2] _·_ Γ[2 _[ℓ][−]_[2] ](2)[sin][2] _[ℓ][−]_[1] _[−]_[1][ �] 2 _ψi_[(] _[ℓ]_[)] �. The goal of quantization to _b_ -bits is to partition the range [0 _, π/_ 2] (or [0 _,_ 2 _π_ ) in case of _ℓ_ = 1) into 2 _[b]_ intervals _I_ 1[(] _[ℓ]_[)] _[, I]_ 2[(] _[ℓ]_[)] _[,][ · · ·][ I]_ 2[(] _[ℓ][b]_[)][and][find][corresponding] centroids _θ_ 1[(] _[ℓ]_[)] _[, θ]_ 2[(] _[ℓ]_[)] _[, . . . θ]_ 2[(] _[ℓ][b]_[)][such][that][the][following][is][mean][squared][error][is][minimized:]

**==> picture [335 x 47] intentionally omitted <==**

This problem is a continuous analog of the k-means clustering problem in dimension 1. Since we have an explicit formula for the p.d.f. of angle _ψi_[(] _[ℓ]_[)] _∼ fℓ_ ( _ψi_[(] _[ℓ]_[)][)][=] 2[2] _[ℓ][−]_[1] Γ _[−]_ ([2] 2 _·[ℓ]_ Γ(2 _[−]_[1] ) _[ℓ][−]_[2] )[2][sin][2] _[ℓ][−]_[1] _[−]_[1][ �] 2 _ψi_[(] _[ℓ]_[)] � the optimal interval partitions and centroids for Eq. (4) can be efficiently computed using numerical

**Algorithm 1** PolarQuant

1: **input:** embedding _**X** ∈_ R _[n][×][d]_ , precondition matrix _**S** ∈_ R _[d][×][d]_ , bit width _b_ `// Cartesian to Polar transform` 2: **R** _i,_ **Ψ**[(1)] _i[, . . . ,]_ **[ Ψ]**[(log] _i_[2] _[ d]_[)] _←_ Polar( _**X** i ·_ _**S**_ ) for _i ∈_ [ _n_ ] `// Codebook Construction` 3: Find partition intervals and centroids ( _Ik_[(] _[ℓ]_[)] _[, θ] k_[(] _[ℓ]_[)][)] _[k][∈]_[[2] _[b]_[]][of] **[ Ψ]**[(] _[ℓ]_[)] _[∈]_[R] _[n][×]_[(] _[d/]_[2] _[ℓ]_[)][that minimize the cost] in Eq. (4) for _ℓ ∈_ [log2 _d_ ] (See Section 4.1 for details) `// Angles Quantization` 4: _**J** i_[(] _[ℓ]_[)] _←_ Quant **Ψ**[(] _i[ℓ]_[)] _[,]_[ (] _[I] k_[(] _[ℓ]_[)] _[, θ] k_[(] _[ℓ]_[)][)] _[k][∈]_[[2] _[b]_[]] for _i ∈_ [ _n_ ] and _ℓ ∈_ [log2 _d_ ] � � 5: **output: R** _∈_ R _[n][×]_[1] _,_ _**J**_[(1)] _∈_ [2 _[b]_ ] _[n][×][d/]_[2] _, . . . ,_ _**J**_[(log][2] _[ d]_[)] _∈_ [2 _[b]_ ] _[n][×]_[1] _,_ ( _Ik_[(] _[ℓ]_[)] _[, θ] k_[(] _[ℓ]_[)][)] _[k][∈]_[[2] _[b]_[]]

6: **Procedure** Polar ( _**y**_ ) 7: _**r**_[(0)] _←_ _**y** ∈_ R _[d]_ 8: **for** _ℓ_ = 1 _, . . . ,_ log2 _d_ **do** 9: **for** _j_ = 1 _, . . . , d/_ 2 _[ℓ]_ **do** 10: _**ψ** j_[(] _[ℓ]_[)] _←_ tan _[−]_[1][ �] _**r**_ 2[(] _[ℓ] j[−]_[1)] _/_ _**r**_ 2[(] _[ℓ] j[−] −_[1)] 1 � ( _ℓ−_ 1) 11: _**r** j_[(] _[ℓ]_[)] _←_ ��� _**r**_ 2 _j−_ 1:2 _j_ ���2 12: **end for** 13: **end for** 14: **output:** _**r**_[(log][2] _[ d]_[)] _,_ _**ψ**_[(1)] _, . . . ,_ _**ψ**_[(log][2] _[ d]_[)] 15: **Procedure** Quant � _**ψ** ,_ ( _Ik, θk_ ) _k∈_ [2 _b_ ]� 16: _**j** i ←_ argmin _k∈_ [2 _b_ ] _|θk −_ _**ψ** i|_ for _i ∈_ [ _d[′]_ ] s.t. _**ψ** ∈_ R _[d][′]_

17: **output:** _**j**_

18: **Procedure** DeQuant( _**r** ,_ ( _**j**_[(] _[ℓ]_[)] ) _ℓ∈_ [log2 _d_ ] _,_ ( _θk_[(] _[ℓ]_[)][)] _[k][∈]_[[2] _[b]_[]] _[,]_ _**[ S]**_[)] 19: **for** _ℓ_ = log2 _d, . . . ,_ 1 **do** 20: **for** _j_ = 1 _, . . . , d/_ 2 _[ℓ]_ **do** 21: _i ←_ _**j** j_[(] _[ℓ]_[)] 22: _**r**_ 2[(] _[ℓ] j[−] −_[1)] 1 _[←]_ _**[r]** j_[(] _[ℓ]_[)] _·_ cos _θi_[(] _[ℓ]_[)] 23: _**r**_[(] _[ℓ][−]_[1)] _←_ _**r**_[(] _[ℓ]_[)] _·_ sin _θ_[(] _[ℓ]_[)] 2 _j j i_ 24: **end for** 25: **end for** 26: **output:** _**r**_[(0)] _·_ _**S**[⊤]_

methods. For example, one can run k-means clustering on the gathered angle values which can be considered samples from the distribution. This approach ensures minimal quantization error for each angle independently and the overall reconstruction error as well.

We provide a pseudocode of PolarQuant in Algorithm 1. Our main result and error bound are proved in the following.

**Theorem 1.** _For a d-dimensional vector_ _**x** ∼ N_ (0 _, Id_ ) _, the polar quantization scheme in Algorithm 1_

_uses O_ (log 1 _/ε_ ) _bits per coordinate + the space necessary to store ∥_ _**x** ∥_ 2 _, while reconstructing a vector_ _**x**[′] from such a representation satisfying_

**==> picture [114 x 13] intentionally omitted <==**

The proof of Theorem 1 can be found in Appendix C. We note that a scheme which uses a deterˆ ministic _ε_ -net _N_ of the unit sphere S _[d][−]_[1] , with _|N|_ = _O_ (1 _/ε_ ) _[d]_ and rounds the vector _**x**_ = _**x** /∥_ _**x** ∥_ 2 also uses _O_ (log 1 _/ε_ ) bits per coordinate while achieving the above bounds in the worst case instead of in expectation over the Gaussian distribution. But our construction (i) gives the flexibility to vary the size of the codebook used per each level depending on the resource constraints and as the above theorem shows, can approach the same quality as pinning to an _ε_ -net on average, (ii) does not need to store a _|N|_ -size codebook which is impractical even for modest sizes of _d_ and (iii) has a fast decoding/encoding implementation.

## **4 KV Cache Quantization with PolarQuant**

In this section, we describe how PolarQuant can be applied to the KV cache problem and our practical implementation. Formally, given a stream of ( _**q**_ 1 _,_ _**k**_ 1 _,_ _**v**_ 1) _, . . . ,_ ( _**q** n,_ _**k** n,_ _**v** n_ ), where _**q** i,_ _**k** i,_ _**v** i ∈_ R _[d]_ are query, key and value embeddings at _i_ -th generation step for all _i ∈_ [ _n_ ]. Let _**K**_ : _i,_ _**V**_ : _i ∈_ R _[i][×][d]_ be matrices defined by stacking _**k**_ 1 _, . . . ,_ _**k** i_ and _**v**_ 1 _, . . . ,_ _**v** j_ in their rows, respectively. The goal is to compute:

**==> picture [298 x 29] intentionally omitted <==**

For an efficient token generation, the KV cache at _i_ -th generation step ( _**K**_ : _i,_ _**V**_ : _i_ ) are stored in the memory. To reduce the memory space, we invoke PolarQuant (Algorithm 1) on these embeddings. Let _**K**_[�] : _i,_ _**V**_[�] : _i ∈_ R _[i][×][d]_ be their dequantizations using DeQuant procedure in Algorithm 1. Then, we estimate Eq. (5) by computing

**==> picture [295 x 34] intentionally omitted <==**

Note that the na¨ıve cache requires _d · b_ FPN memory space to store each _d_ -dimensional embedding where _b_ FPN is the number of bits to represent a single floating-point number. If we quantize log2 _d_ level angles with _b_ bits each and keep centroids in _b_ FPN bits, the memory space becomes ( _b_ FPN + ( _d −_ 1) _b_ ). For example, `Llama` - `3` _._ `1` - `8B` - `Instruct` is represented by _b_ FPN = 16 bits and has _d_ = 128. For _b_ = 3, we can save the memory space 4 _._ 008 times. In Section 5, the PolarQuant with KV cache marginally degrades the performance of LLMs on various tasks.

## **4.1 Practical Implementation**

The PolarQuant algorithm recursively reduces the dimension of radii by half until the input has dimension 1. We recurse on the polar transformation for a constant _L_ = 4 levels. Thus, for an embedding of dimension _d_ , we obtain _d/_ 16-dimensional radii and 15 _d/_ 16 angle values. We also

**==> picture [227 x 179] intentionally omitted <==**

**==> picture [226 x 179] intentionally omitted <==**

**==> picture [381 x 11] intentionally omitted <==**

**----- Start of picture text -----**<br>
(a) without random preconditioning (b) with random preconditioning<br>**----- End of picture text -----**<br>

Figure 2: Distributions of angles of polar transformed key embeddings (a) with and (b) without random preconditioning. Preconditioning flattens the angle distribution and removes outliers which allows angle quantization more accurately.

define different numbers of bits for each quantization level: _b_ = 4 bits for the first level, and _b_ = 2 bits for the remaining levels. This is because the range of angle at the first level [0 _,_ 2 _π_ ) is 4 times wider than the others [0 _, π/_ 2]. Consequently, the representation of a block of 16 coordinates uses _b_ FPN + 32 + 8 + 4 + 2 = _b_ FPN + 46 bits that translates to 62 _/_ 16 = 3 _._ 875 bits per coordinate when _b_ FPN = 16 bits.

We implement PolarQuant using the Pytorch [31] framework. Since the smallest data type is represented in 8 bits ( `torch` _._ `uint8` ), we pack quantized angle indices into 8-bit unit. To accelerate computation on GPU clusters, we implement CUDA kernels for two key operations: (1) the product of query vectors with the dequantized key cache, i.e., _**K**_[�] : _i ·_ _**q** i_ , and (2) the product of attention scores with the dequantized value cache as per Eq. (6). For the preconditioning matrix _**S**_ , we generate a random rotational matrix. The matrix _**S**_ is shared across key and value embeddings, as well as all layers and attention heads in the Transformer architecture.

For angle codebook construction (line 3 in Algorithm 1), we use the 1-D k-means++ clustering on either online angles obtained from polar-transformed inputs or offline precomputed angles. Both approaches approximate the solution to Eq. (4) by discretizing with samples from angle distributions. While online approach requires additional clustering computation during every prefill stage, this onetime cost is offset by improved performance compared to the offline approach. We present detailed runtime and performance comparisons in Section 5.

## **5 Experiments**

All experiments are performed with a single NVIDIA RTX A6000 GPU with 48GB VRAM.

**==> picture [142 x 95] intentionally omitted <==**

**==> picture [142 x 95] intentionally omitted <==**

**==> picture [142 x 95] intentionally omitted <==**

**==> picture [432 x 122] intentionally omitted <==**

**----- Start of picture text -----**<br>
(a) Exact (16 bits), Score: 0 . 995 (b) SnapKV, Score: 0 . 858 (c) PyramidKV, Score: 0 . 891<br>(d) KIVI, Score: 0 . 984 (e) PolarQuant, Score: 0 . 991 (f) PolarQuant-R, Score: 0 . 990<br>**----- End of picture text -----**<br>

Figure 3: Needle-In-A-Haystack test using `Llama` - `3` _._ `1` - `8B` - `Instruct` . The test spans different depths and context lengths ranging from 4K to 104K. Green/red colors indicate high/low recall scores (higher is better). PolarQuant shows the best performance.

## **5.1 Random Precondition on KV Cache**

We first explore the effectiveness of preconditioning. In particular, we choose a single prompt from Qasper dataset in LongBench [5] and extract the corresponding KV cache. To observe how preconditioning improves, we transform the KV cache into 4-level polar coordinates and plot their angle distributions of the key cache. Note that the first level angles are range in [0 _,_ 2 _π_ ) and the rest are in [0 _, π/_ 2]. The results are illustrated in Fig. 2. As shown in Lemma 2, the distribution of angles get predictably sharper around _π/_ 4 as the level increases. Moreover, we observe that at the first level the preconditioning flattens the angle distribution and removes outliers. This allows us to quantize angles in the KV cache more accurately.

## **5.2 Needle-In-A-Haystack**

Next we evaluate our method for the “Needle-In-A-Haystack” test [19]. It asks the model to retrieve the information in a given sentence where the sentence (the “needle”) is placed in an arbitrary location of a long document (the “haystack”). We follow the same setting from Fu et al. [14] and use the `Llama` - `3` _._ `1` - `8B` - `Instruct` to run the test. We vary the input sequence lengths from 4K to 104K. The evaluation is based on the recall score by comparing the hidden sentence. We compare PolarQuant to SnapKV [24], PyramidKV [8] and KIVI [26], where we use their implementations from [18]. All methods are set to a compression ratio of 0 _._ 25, i.e., required memory is _×_ 0 _._ 25 the full KV cache. Specifically, we run our algorithm with and without the preconditioning and refer to them as PolarQuant-R and PolarQuant, respectively. In Fig. 3, we observe that quantization methods (e.g., KIVI, PolarQuant) outperform token-level compression methods (e.g., SnapKV, PyramidKV). PolarQuant shows better scores than KIVI. Additionally, PolarQuant shows a marginally better score than PolarQuant-R.

Table 1: LongBench-V1 [5] results of various KV cache compression methods on `Llama` - `3` _._ `1` - `8B` - `Instruct` . The best values among compression methods are indicated in **bold** .

| Method                | SQA       | MQA       | Sum       | Task | Few       | Syn       | Code      | Average   |
| --------------------- | --------- | --------- | --------- | ---- | --------- | --------- | --------- | --------- |
| Exact (16 bits)       | 45.71     | 45.32     | 26.69     |      | 68.62     | 59.25     | 46.17     | 48.63     |
| Snapkv                | 38.23     | 42.61     | 19.07     |      | 64.65     | 59.60     | 43.28     | 44.57     |
| HeadKV                | 39.45     | 42.69     | 19.77     |      | 68.07     | 59.48     | 42.60     | 45.34     |
| PyramidKV             | 36.80     | 41.54     | 18.91     |      | 64.88     | 59.68     | 42.38     | 44.03     |
| StreamingLLM          | 25.68     | 35.79     | 20.90     |      | 56.91     | 58.81     | 32.07     | 38.36     |
| KIVI                  | 43.38     | 37.81     | **27.44** |      | 68.60     | 58.67     | 44.29     | 46.70     |
| PolarQuant            | 44.03     | 44.34     | 27.32     |      | **68.68** | **59.82** | 44.46     | 48.11     |
| PolarQuant-R (ofine)  | 44.71     | 44.72     | 26.43     |      | 68.58     | 60.08     | **45.20** | 48.29     |
| PolarQuant-R (online) | **45.45** | **45.13** | 26.42     |      | 68.54     | 59.57     | 45.13     | **48.37** |

## **5.3 End-to-end Generation on LongBench**

We run various KV cache compression algorithms for LongBench datasets [5], which encompasses diverse long-text scenarios including single/multi-document question-answering (SQA/MQA), summarization (Sum), few-shot learning (Few), synthetic tasks (Syn), and code completion (Code). Since the number of generated tokens is small compared to the input sequence length across all datasets, we preserve all new streamed query, key, and value pairs from the generation stage in full precision (16 bits) for all methods. We evaluate PolarQuant against the baseline methods using in Section 5.2 as well as StreamingLLM [38] and HeadKV [13] on `Llama` - `3` _._ `1` - `8B` - `Instruct` .

We investigate two variants of PolarQuant-R: one using online codebook construction and another using offline one discussed in Section 4.1. The online variant performs clustering for each individual input prompt and layer, while the offline one employs a single precomputed codebook that is shared across all input prompts, layers, and attention heads. This offline approach is supported by our findings that the angle distribution, when preconditioned, remains consistent regardless of the input.

As reported in Table 1, our methods achieve superior performance compared to other methods, i.e., the average performance scores are higher by a large margin. This justifies the performance benefits of the quantization of polar coordinates. Moreover, the preconditioned variants (PolarQuant-R) generally demonstrates better performance than the non-preconditioned version. Among them, the online variant performs slightly better than the offline one.

## **5.4 Runtime Analysis**

We evaluate wall-clock runtimes of both prefill and token generation stages. Using the Llama model with an input prompt length of 16 _,_ 384, we measure the time to generate 1 _,_ 024 tokens for each method. Table 2 summaries the result. Token eviction approaches (SnapKV, PyramidKV, and HeadKV) demonstrate faster generation times compared to exact and quantization methods, though at the cost of lower quality. Among quantization approaches, our PolarQuant algorithms achieve 14% faster generation time than the KIVI while maintaining superior performance. These

Table 2: Wall-clock runtime comparisons of various KV cache compression methods. The input sequence length is _n_ = 16 _,_ 384 and the number of generated tokens is 1 _,_ 024.

| Method                | Prefll Time (sec) | Generation Time (sec) |
| --------------------- | ----------------- | --------------------- |
| Exact (16 bits)       | 2.934             | 38.374                |
| SnapKV                | 3.438             | 34.053                |
| PyramidKV             | 3.428             | 32.732                |
| HeadKV                | 3.300             | 34.401                |
| KIVI                  | 3.590             | 49.564                |
| PolarQuant            | 11.623            | 43.652                |
| PolarQuant-R (online) | 11.633            | 44.448                |
| PolarQuant-R (ofine)  | 3.364             | 44.097                |

results demonstrate that PolarQuant offers advantages in both computational efficiency and model performance. To achieve faster prefill times, we recommend using offline codebook construction, as it significantly reduces runtime by eliminating the need for clustering, though this results in a modest performance trade-off. We leave even better codebook construction approaches for future research.

## **6 Conclusion**

We propose PolarQuant, a novel quantization method applied to angles in polar coordinates. We connect it to the random preconditioning which allows us to formalize angle distribution to be quantized. We provide rigorous theoretical bounds on quantization error. When applied to the KV cache compression problem, PolarQuant significantly reduces memory requirements during LLM inference while maintaining model performance. The principles underlying our method extend beyond KV cache compression, offering potential applications in LLM weight quantization and general vector similarity search problems.

## **References**

* [1] Achiam, J., Adler, S., Agarwal, S., Ahmad, L., Akkaya, I., Aleman, F. L., Almeida, D., Altenschmidt, J., Altman, S., Anadkat, S., et al. Gpt-4 technical report. _arXiv preprint arXiv:2303.08774_ , 2023.

* [2] Ainslie, J., Lee-Thorp, J., de Jong, M., Zemlyanskiy, Y., Lebron, F., and Sanghai, S. Gqa: Training generalized multi-query transformer models from multi-head checkpoints. In _Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing_ , pp. 4895–4901, 2023.

* [3] Anthropic. Claude, 2024. `https://www.anthropic.com/news/claude-3-family` .

* [4] Ashkboos, S., Mohtashami, A., Croci, M. L., Li, B., Cameron, P., Jaggi, M., Alistarh, D.,

Hoefler, T., and Hensman, J. Quarot: Outlier-free 4-bit inference in rotated llms. _arXiv preprint arXiv:2404.00456_ , 2024.

* [5] Bai, Y., Lv, X., Zhang, J., Lyu, H., Tang, J., Huang, Z., Du, Z., Liu, X., Zeng, A., Hou, L., Dong, Y., Tang, J., and Li, J. Longbench: A bilingual, multitask benchmark for long context understanding. _arXiv preprint arXiv:2308.14508_ , 2023.

* [6] Beltagy, I., Peters, M. E., and Cohan, A. Longformer: The long-document transformer. _arXiv preprint arXiv:2004.05150_ , 2020.

* [7] Bhattacharya, A., Freund, Y., and Jaiswal, R. On the k-means/median cost function. _Information Processing Letters_ , 177:106252, 2022. URL `https://arxiv.org/pdf/1704.05232` .

* [8] Cai, Z., Zhang, Y., Gao, B., Liu, Y., Liu, T., Lu, K., Xiong, W., Dong, Y., Chang, B., Hu, J., et al. Pyramidkv: Dynamic kv cache compression based on pyramidal information funneling. _arXiv preprint arXiv:2406.02069_ , 2024.

* [9] Dai, D., Deng, C., Zhao, C., Xu, R., Gao, H., Chen, D., Li, J., Zeng, W., Yu, X., Wu, Y., et al. Deepseekmoe: Towards ultimate expert specialization in mixture-of-experts language models. _arXiv preprint arXiv:2401.06066_ , 2024.

* [10] Dasgupta, S. and Gupta, A. An elementary proof of a theorem of johnson and lindenstrauss. _Random Structures & Algorithms_ , 22(1):60–65, 2003.

* [11] Dong, S., Cheng, W., Qin, J., and Wang, W. Qaq: Quality adaptive quantization for llm kv cache. _arXiv preprint arXiv:2403.04643_ , 2024.

* [12] FireFly. Adobe firefly, 2023. `https://firefly.adobe.com/` .

* [13] Fu, Y., Cai, Z., Asi, A., Xiong, W., Dong, Y., and Xiao, W. Not all heads matter: A headlevel kv cache compression method with integrated retrieval and reasoning. _arXiv preprint arXiv:2410.19258_ , 2024.

* [14] Fu, Y., Panda, R., Niu, X., Yue, X., Hajishirzi, H., Kim, Y., and Peng, H. Data engineering for scaling language models to 128k context. _arXiv preprint arXiv:2402.10171_ , 2024. URL `https://github.com/FranxYao/Long-Context-Data-Engineering` .

* [15] Google. Gemini 1.5 pro, 2024. `https://arxiv.org/abs/2403.05530` .

* [16] Google. Veo 2, 2024. `https://deepmind.google/technologies/veo/veo-2/` .

* [17] Hooper, C., Kim, S., Mohammadzadeh, H., Mahoney, M. W., Shao, Y. S., Keutzer, K., and Gholami, A. Kvquant: Towards 10 million context length llm inference with kv cache quantization. _arXiv preprint arXiv:2401.18079_ , 2024.

* [18] Jiang, H., LI, Y., Zhang, C., Wu, Q., Luo, X., Ahn, S., Han, Z., Abdi, A. H., Li, D., Lin, C.-Y., et al. Minference 1.0: Accelerating pre-filling for long-context llms via dynamic sparse attention. In _The Thirty-eighth Annual Conference on Neural Information Processing Systems_ , 2024.

* [19] Kamradt, G. Needle in a haystack - pressure testing llms., 2023. `https://github.com/ gkamradt/LLMTest_NeedleInAHaystack` .

* [20] Kang, H., Zhang, Q., Kundu, S., Jeong, G., Liu, Z., Krishna, T., and Zhao, T. Gear: An efficient kv cache compression recipefor near-lossless generative inference of llm. _arXiv preprint arXiv:2403.05527_ , 2024.

* [21] Kaplan, J., McCandlish, S., Henighan, T., Brown, T. B., Chess, B., Child, R., Gray, S., Radford, A., Wu, J., and Amodei, D. Scaling laws for neural language models. _arXiv preprint arXiv:2001.08361_ , 2020.

* [22] Kim, J., Park, J., Cho, J., and Papailiopoulos, D. Lexico: Extreme kv cache compression via sparse coding over universal dictionaries. _arXiv preprint arXiv:2412.08890_ , 2024.

* [23] Kwon, W., Li, Z., Zhuang, S., Sheng, Y., Zheng, L., Yu, C. H., Gonzalez, J., Zhang, H., and Stoica, I. Efficient memory management for large language model serving with pagedattention. In _Proceedings of the 29th Symposium on Operating Systems Principles_ , pp. 611–626, 2023.

* [24] Li, Y., Huang, Y., Yang, B., Venkitesh, B., Locatelli, A., Ye, H., Cai, T., Lewis, P., and Chen, D. Snapkv: Llm knows what you are looking for before generation. _arXiv preprint arXiv:2404.14469_ , 2024.

* [25] Liu, Z., Desai, A., Liao, F., Wang, W., Xie, V., Xu, Z., Kyrillidis, A., and Shrivastava, A. Scissorhands: Exploiting the persistence of importance hypothesis for llm kv cache compression at test time. _Advances in Neural Information Processing Systems_ , 36, 2024.

* [26] Liu, Z., Yuan, J., Jin, H., Zhong, S., Xu, Z., Braverman, V., Chen, B., and Hu, X. Kivi: A tuning-free asymmetric 2bit quantization for kv cache. _arXiv preprint arXiv:2402.02750_ , 2024.

* [27] Microsoft Copilot. Microsoft copilot, 2023. `https://github.com/features/copilot` .

* [28] Midjourney. Midjourney, 2022. `https://www.midjourney.com/home` .

* [29] OpenAI. Introducing gpt-4o, 2024. `https://openai.com/index/hello-gpt-4o/` .

* [30] OpenAI. Sora: Creating video from text, 2024. `https://openai.com/index/sora/` .

* [31] Paszke, A., Gross, S., Massa, F., Lerer, A., Bradbury, J., Chanan, G., Killeen, T., Lin, Z., Gimelshein, N., Antiga, L., et al. Pytorch: An imperative style, high-performance deep learning library. _Advances in neural information processing systems_ , 32, 2019.

* [32] Ramesh, A., Dhariwal, P., Nichol, A., Chu, C., and Chen, M. Hierarchical text-conditional image generation with clip latents. _arXiv preprint arXiv:2204.06125_ , 2022.

* [33] Shah, J., Bikshandi, G., Zhang, Y., Thakkar, V., Ramani, P., and Dao, T. Flashattention3: Fast and accurate attention with asynchrony and low-precision. _arXiv preprint arXiv:2407.08608_ , 2024.

* [34] Shazeer, N. Fast transformer decoding: One write-head is all you need. _arXiv preprint arXiv:1911.02150_ , 2019.

* [35] Sheng, Y., Zheng, L., Yuan, B., Li, Z., Ryabinin, M., Chen, B., Liang, P., R´e, C., Stoica, I., and Zhang, C. Flexgen: High-throughput generative inference of large language models with a single gpu. In _International Conference on Machine Learning_ , pp. 31094–31116. PMLR, 2023.

* [36] Sun, H., Chang, L.-W., Bao, W., Zheng, S., Zheng, N., Liu, X., Dong, H., Chi, Y., and Chen, B. Shadowkv: Kv cache in shadows for high-throughput long-context llm inference. _arXiv preprint arXiv:2410.21465_ , 2024.

* [37] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, L., and Polosukhin, I. Attention is all you need. _NeurIPS_ , 2017.

* [38] Xiao, G., Tian, Y., Chen, B., Han, S., and Lewis, M. Efficient streaming language models with attention sinks. _arXiv preprint arXiv:2309.17453_ , 2023.

* [39] Yang, J. Y., Kim, B., Bae, J., Kwon, B., Park, G., Yang, E., Kwon, S. J., and Lee, D. No token left behind: Reliable kv cache compression via importance-aware mixed precision quantization. _arXiv preprint arXiv:2402.18096_ , 2024.

* [40] Yue, Y., Yuan, Z., Duanmu, H., Zhou, S., Wu, J., and Nie, L. Wkvquant: Quantizing weight and key/value cache for large language models gains more. _arXiv preprint arXiv:2402.12065_ , 2024.

* [41] Zandieh, A., Daliri, M., and Han, I. Qjl: 1-bit quantized jl transform for kv cache quantization with zero overhead. _arXiv preprint arXiv:2406.03482_ , 2024.

* [42] Zandieh, A., Han, I., Mirrokni, V., and Karbasi, A. Subgen: Token generation in sublinear time and memory. _arXiv preprint arXiv:2402.06082_ , 2024.

* [43] Zhang, T., Yi, J., Xu, Z., and Shrivastava, A. Kv cache is 1 bit per channel: Efficient large language model inference with coupled quantization. _arXiv preprint arXiv:2405.03917_ , 2024.

* [44] Zhang, Z., Sheng, Y., Zhou, T., Chen, T., Zheng, L., Cai, R., Song, Z., Tian, Y., R´e, C., Barrett, C., et al. H2o: Heavy-hitter oracle for efficient generative inference of large language models. _Advances in Neural Information Processing Systems_ , 36, 2024.

## **A Proof of Fact 1**

_Proof._ The cumulative distribution function (c.d.f) of the random variable _R_ can be computed as follows:

**==> picture [218 x 46] intentionally omitted <==**

where the last equality is because the squared norm of _**x**_ , by definition, is Chi-squared random variable. Differentiating the above c.d.f gives us the p.d.f of _R_ :

**==> picture [188 x 26] intentionally omitted <==**

## **B Error Bounds for Polar Quantization**

**Lemma 3.** _If X and Y are independent non-negative random variables that are sampled from the generalized gamma distribution with probability density function fZ_ ( _z_ ) = 2 _[d/]_[2] _·_ Γ(2 _d/_ 2) _[z][d][−]_[1][ exp(] _[−][z]_[2] _[/]_[2)] _so that X_[2] _, Y_[2] _∼ χ_[2] _d[,][then][the][distribution][of]_[Θ = tan] _[−]_[1][(] _[Y/X]_[)] _[has][the][pdf]_

**==> picture [234 x 26] intentionally omitted <==**

**==> picture [331 x 14] intentionally omitted <==**

_Proof._ Since _X_ and _Y_ are i.i.d., their joint distribution function is the following:

**==> picture [364 x 30] intentionally omitted <==**

Now by changing the coordinates from Cartesian to polar we can represent the above distribution as a joint distribution over variables _r_ = ~~�~~ _x_[2] + _y_[2] _, θ_ = tan _[−]_[1] ( _y/x_ ) with _r ≥_ 0 and _θ ∈_ [0 _, π/_ 2) as follows:

**==> picture [372 x 28] intentionally omitted <==**

Since the joint probability distribution of _r, θ_ is a separable function, we can deduce the marginal

probability distribution of _θ_ as follows:

**==> picture [241 x 152] intentionally omitted <==**

where the last equality above follows from Fact 2. For a proof of the mean and variance bound see Lemma 3.

From the symmetry of _f_ Θ( _·_ ) around _θ_ = _π/_ 4, it is clear that _µ_ Θ = _π/_ 4. We now bound _σ_ Θ.

**==> picture [422 x 221] intentionally omitted <==**

Substituting _β_ = 8( _d −_ 1) _θ_[2] _/π_[2] , we have

**==> picture [424 x 81] intentionally omitted <==**

Assuming _d_ is even and using Stirling approximation, we get

Therefore,

**==> picture [171 x 28] intentionally omitted <==**

where _C[′′]_ is a universal constant independent of _d_ hence proving the theorem.

## **C Proof of Theorem 1**

Suppose that _X, Y_ are random variables as in Lemma 3 so that _X_[2] _, Y_[2] _∼ χ_[2] _d_[and][define] _[R]_[=] _√X_[2] + _Y_[2] and Θ = tan _[−]_[1] ( _Y/X_ ). Let _{θ_ 1 _, . . . , θk} ⊆_ [0 _, π/_ 2] be a codebook and define Θ _[′]_ = round(Θ) to be the _θi_ nearest to Θ and _R[′]_ be an approximation of _R_ . We then define

**==> picture [288 x 13] intentionally omitted <==**

to be the reconstructions of _X_ and _Y_ respectively from the rounding scheme, which rounds Θ using the codebook and the radius _R_ using a recursive approximation. The reconstruction error is defined as

**==> picture [110 x 14] intentionally omitted <==**

**==> picture [255 x 13] intentionally omitted <==**

**==> picture [487 x 13] intentionally omitted <==**

Using the fact that 2 _ab ≤_ (1 _/α_ ) _· a_[2] + _α · b_[2] for any _α >_ 0, we get [ _a_ + _b_ ](2) = _a_[2] + 2 _ab_ + _b_[2] _≤_ (1 + 1 _/α_ ) _a_[2] + (1 + _α_ ) _b_[2] for any _α >_ 0. Therefore we have that for any _α >_ 0,

**==> picture [427 x 49] intentionally omitted <==**

where we used that fact that sin( _·_ ) and cos( _·_ ) are 1-Lipschitz and that sin[2] (Θ _[′]_ ) + cos[2] (Θ _[′]_ ) = 1.

Now, restricting _α ∈_ (0 _,_ 1) we get that

**==> picture [344 x 25] intentionally omitted <==**

using the independence of _R_ and Θ and the fact that Θ _[′]_ is a deterministic function of Θ given the codebook _{θ_ 1 _, . . . , θk}_ .

When _d_ = 1, we call E[[ _X − X[′]_ ](2) + [ _Y − Y[′]_ ](2) ] to be error0 since it is the expected error in the reconstruction at level 0 and similarly, we call E[[ _R − R[′]_ ](2) ] = error1 since it is the error in level 1. We also call E[[Θ _−_ Θ _[′]_ ](2) ] = quant1 since it is the error of quantizing angles in that level. We therefore have

**==> picture [206 x 26] intentionally omitted <==**

Given a vector ( _X_ 1 _, . . . , Xd_ ), where each _Xi ∼ N_ (0 _,_ 1), let ( _X_ 1 _[′][, . . . , X] d[′]_[) be the reconstructions using] _t_ = log2( _d_ )-level quantization as described in the introduction. Extending the above definitions, we say that error _i_ is the total expected error in the reconstructions of level _i_ coordinates in the quantization scheme. Using the above, inequality, we get

**==> picture [544 x 23] intentionally omitted <==**

where we use the fact that E[ _X_ 1[2][+] _[ · · ·]_[ +] _[ X] d_[2][]][=] _[d]_[.][Since][we][store][the][top-level][radius][exactly,][we] have error _t_ +1 = 0 and therefore,

**==> picture [307 x 23] intentionally omitted <==**

For each level _i_ , given _ε >_ 0, we will now upper bound the size of the codebook for level _i_ so that quant _i ≤ ε_ . It is clear that a codebook _{_ 0 _,[√] ε,_ 2 _[√] ε, . . . ,_ 2 _π}_ has a size _⌈_ 2 _π/[√] ε⌉_ + 1 and has quant _i ≤ ε_ irrespective of the distribution of the angles. We would like to use the fact that the distribution of angles gets concentrated with increasing level _i_ to obtain better bounds on the size of the codebook. To that end, we prove the following lemma.

**Lemma 4.** _Let X ∈_ [0 _, π/_ 2] _be an arbitrary random variable with Var_ ( _X_ ) = _σ_[2] _. Given x and a set S_ = _{x_ 1 _, . . . , xk}, define d_ ( _x, S_ ) = min _i∈_ [ _k_ ] _|xi − x|. Define_

**==> picture [148 x 20] intentionally omitted <==**

_Given ε >_ 0 _, for k_ = Ω(log(1 _/σ_ ) _/[√] ε_ ) _, we have Vark_ ( _X_ ) _≤ ε · Var_ 1( _X_ ) = _ε · σ_[2] _._

The lemma shows that as variance decreases, we can get tighter approximation bounds using the same value of _k_ . The proof of this lemma is similar to that of Lemma 2 in Bhattacharya et al. [7].

_Proof._ Let _µ_ = E[ _X_ ]. Consider the interval [ _µ − σ, µ_ + _σ_ ] and consider the points _S_ 1 = _{µ, µ ± εσ, µ ±_ 2 _εσ, . . . , µ ± σ}_ . Note that _|S_ 1 _|_ = 3 + 2 _/ε_ . We have

**==> picture [192 x 14] intentionally omitted <==**

since every point in the interval [ _µ − σ, µ_ + _σ_ ] has some point in _S_ 1 that is at most _εσ_ away.

Now define _S_ 2 = _{µ ±_ [1 + _ε_ ](0) _σ, µ ±_ [1 + _ε_ ](1) _σ, . . . , }_ where the exponent _i_ extends until we have _µ_ + (1 + _ε_ ) _[i] σ ≥ π/_ 2 and _µ −_ (1 + _ε_ ) _[i] σ ≤_ 0. Note that we have _|S_ 2 _| ≤ O_ (log(1 _/σ_ ) _/ε_ ). Suppose _|X − µ| ∈_ [(1 + _ε_ ) _[i] σ,_ (1 + _ε_ ) _[i]_[+1] _σ_ ], then _d_ ( _X, S_ 2) _≤ ε_ (1 + _ε_ ) _[i] σ ≤ ε|X − µ|_ . Now,

**==> picture [244 x 13] intentionally omitted <==**

Thus by putting _ε_ := ~~�~~ _ε/_ 2 above, if _k_ = Ω(log(1 _/σ_ ) _/[√] ε_ ), then Var _k_ ( _X_ ) _≤ εσ_[2] .

Now we consider bounding quant _i_ by picking an appropriate codebook for level _i_ . For all _i >_ 0, given a codebook _C_ = _{θ_ 1 _, . . . θ|C|}_ , we have quant _i_ = E[(Θ _−_ round(Θ _, C_ ))[2] ] where Θ is arctan( _Y/X_ ) with _Y_[2] _, X_[2] _∼ χ_[2] 2 _[i][−]_[1][.][From][the][lemma][above,][when] _[i][>]_[1,][we][have][Var(Θ)] _[≤][C/]_[(2] _[i][−]_[1] _[−]_[1)][and] hence, the above lemma shows that there exists a codebook _C_ of size _|C|_ = Θ( _i/[√] ε_ ),

**==> picture [272 x 21] intentionally omitted <==**

If we use a codebook of size _O_ (1 _/[√] ε_ ) for level 1, we have quant1 _≤ ε_ and as described above, for _i ≥_ 1, if we use a codebook of size _|C|_ = Θ( _i/[√] ε_ ), then quant _i ≤ ε/_ (2 _[i][−]_[1] ) from which we obtain that

**==> picture [281 x 30] intentionally omitted <==**

picking _α_ = 1 _/_ 2. Now we compute the number of bits necessary to store the quantized representation of a _d_ -dimensional vector. In level _i_ , we have _d/_ 2 _[i]_ independent samples of Θ to be quantized and therefore, we need to store _O_ ( 2 _[d][i]_[log(] _[i/][√] ε_ )) bits for indexing into the codebook for level _i_ . Adding over all the levels, we store _O_ ( _d_ log 1 _/[√] ε_ ) bits for representing the _d_ -dimensional vector and therefore _O_ (log 1 _/ε_ ) bits per coordinate to achieve an average reconstruction error of _ε_ .
